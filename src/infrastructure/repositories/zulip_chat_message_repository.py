from domain.ports.chat_message_repository import ChatMessageRepository
from domain.entities.user import User
from domain.entities.chat_message import ChatMessage
from typing import List, Dict
import zulip
from infrastructure.config.zulip_config import ZulipConfig
from datetime import datetime
from typing import Optional
from infrastructure.repositories.mappers.zulip_mapper import ZulipMapper
import json
from domain.entities.channel import Channel

class ZulipChatMessageRepository(ChatMessageRepository):
    CONTEXT_LOOKBACK_MESSAGES = 20

    def __init__(self):
        self.config = ZulipConfig()
        self.client = zulip.Client(
            email=self.config.email,
            api_key=self.config.api_key,
            site=self.config.site,
        )
        self.mapper = ZulipMapper()

    def __group_unread_messages(self, messages: List[ChatMessage]) -> Dict[str, Channel]:
        # Group unread messages by stream topic or private conversation.
        channels = {}
        if hasattr(self, '_raw_messages'):
            for raw_msg, mapped_msg in zip(self._raw_messages, messages):
                msg_type = raw_msg.get("type")

                if msg_type == "stream":
                    stream_id_value = raw_msg.get("stream_id")
                    if stream_id_value is None:
                        print(f"[WARNING] Skipping stream message without stream_id: message_id={raw_msg.get('id')}")
                        continue

                    stream_id = str(stream_id_value).strip()
                    if not stream_id:
                        print(f"[WARNING] Skipping stream message with empty stream_id: message_id={raw_msg.get('id')}")
                        continue

                    topic = raw_msg.get("subject", "")
                    channel_key = f"stream:{stream_id}:{topic}"
                    channel_id = stream_id
                else:
                    # Zulip direct/private messages.
                    sender_email = (raw_msg.get("sender_email") or "").strip()
                    if not sender_email:
                        print(f"[WARNING] Skipping private message without sender_email: message_id={raw_msg.get('id')}")
                        continue

                    channel_key = f"pm:{sender_email.lower()}"
                    channel_id = channel_key
                    topic = "Direct Message"

                if channel_key not in channels:
                    channels[channel_key] = Channel(channel_id, topic, [], self)

                channels[channel_key].add_message(mapped_msg)

        return channels
    
    def get_messages_from_channel(self, channel: Channel) -> List[ChatMessage]:
        if str(channel.get_id()).startswith("pm:"):
            recipient_email = channel.get_id().split("pm:", 1)[1]
            response = self.client.get_messages({
                "anchor": "newest",
                "num_before": self.CONTEXT_LOOKBACK_MESSAGES,
                "num_after": 0,
                "narrow": [
                    {"operator": "pm-with", "operand": recipient_email},
                ],
                "apply_markdown": True,
                "include_anchor": True,
                "include_history": True,
            })
            if response.get("result") != "success":
                raise RuntimeError(f"Zulip API error: {response.get('msg')}")
            return [self.mapper.to_chat_message(msg) for msg in response.get("messages", [])]

        response = self.client.get_messages({
            "anchor": "newest",
            "num_before": self.CONTEXT_LOOKBACK_MESSAGES,
            "num_after": 0,
            "narrow": [
                {"operator": "stream", "operand": channel.get_id()},
                {"operator": "topic", "operand": channel.get_topic()},
            ],
            "apply_markdown": True,
            "include_anchor": True,
            "include_history": True,
        })
        if response.get("result") != "success":
            raise RuntimeError(f"Zulip API error: {response.get('msg')}")
        return [self.mapper.to_chat_message(msg) for msg in response.get("messages", [])]

    def _dedupe_and_order_messages(self, messages: List[ChatMessage]) -> List[ChatMessage]:
        by_id = {}
        for msg in messages:
            if hasattr(msg, "id"):
                by_id[msg.id] = msg
        ordered = list(by_id.values())
        def _sort_key(msg: ChatMessage):
            created_at = getattr(msg, "created_at", None)
            created_ts = 0.0
            if hasattr(created_at, "timestamp"):
                try:
                    created_ts = float(created_at.timestamp())
                except Exception:
                    created_ts = 0.0
            msg_id = getattr(msg, "id", 0)
            try:
                msg_id = int(msg_id)
            except Exception:
                msg_id = 0
            return (created_ts, msg_id)
        ordered.sort(key=_sort_key)
        return ordered

    def get_streams_with_unread_messages(self) -> Dict[str, Channel]:
        messages = self.get_unread_messages()
        channels = self.__group_unread_messages(messages)
        for channel in channels.values():
            history_messages = self.get_messages_from_channel(channel)
            merged = self._dedupe_and_order_messages(channel.get_messages() + history_messages)
            channel.messages = merged
        return channels

    def get_unread_messages(self) -> List[ChatMessage]:
        params = {
            "anchor": "first_unread",
            "num_before": 0,
            "num_after": 200,
            "use_first_unread_anchor": True,
            "narrow": [
                {"operator": "is", "operand": "unread"},
            ],
            "apply_markdown": True,
            "include_anchor": True,
            "include_history": True,
        }

        response = self.client.get_messages(params)
        if response.get("result") != "success":
            print(f"[ERROR] Zulip GET_MESSAGES failed: {response.get('msg')}")
            raise RuntimeError(f"Zulip API error: {response.get('msg')}")

        messages = response.get("messages", [])
        if messages:
            print(f"[DEBUG] Zulip found {len(messages)} unread messages for {self.config.email}")
        
        # Store the original messages for channel grouping
        self._raw_messages = messages
        return [self.mapper.to_chat_message(msg) for msg in messages]
    
    def send_private_message(self, message: str, user: User):
        recipient_user_id = self._find_user_id_by_email(user.email)
        if recipient_user_id is None:
            raise ValueError(f"Recipient not found in Zulip realm for email: {user.email}")

        request = {
            "type": "private",
            "to": [recipient_user_id],
            "content": message,
        }
        response = self.client.send_message(request)
        if response.get("result") != "success":
            raise RuntimeError(f"Zulip API error: {response.get('msg')}")

    def send_channel_message(self, message: str, channel_id: str, topic: str):
        if str(channel_id).startswith("pm:"):
            recipient_email = channel_id.split("pm:", 1)[1]
            recipient_user_id = self._find_user_id_by_email(recipient_email)
            if recipient_user_id is None:
                raise ValueError(f"Recipient not found in Zulip realm for email: {recipient_email}")
            request = {
                "type": "private",
                "to": [recipient_user_id],
                "content": message,
            }
            response = self.client.send_message(request)
            if response.get("result") != "success":
                raise RuntimeError(f"Zulip API error: {response.get('msg')}")
            return

        if not str(channel_id).strip():
            raise ValueError("Cannot send stream message without channel_id")

        request = {
            "type": "stream",
            "to": channel_id,
            "content": message,
            "subject": topic,
        }
        response = self.client.send_message(request)
        if response.get("result") != "success":
            raise RuntimeError(f"Zulip API error: {response.get('msg')}")

    def send_thread_message(self, message: str, thread_id: str, topic: str):
        request = {
            "type": "stream",
            "to": thread_id,
            "content": message,
            "subject": topic,
        }
        response = self.client.send_message(request)
        if response.get("result") != "success":
            raise RuntimeError(f"Zulip API error: {response.get('msg')}")

    def mark_as_read(self, channel: Channel):
        if str(channel.get_id()).startswith("pm:"):
            message_ids = [m.id for m in channel.get_messages() if hasattr(m, "id")]
            if not message_ids:
                return
            response = self.client.call_endpoint(
                url="messages/flags",
                method="POST",
                request={
                    "messages": message_ids,
                    "op": "add",
                    "flag": "read",
                },
            )
            if response.get("result") != "success":
                raise RuntimeError(f"Zulip API error: {response.get('msg')}")
            return

        response = self.client.mark_stream_as_read(channel.get_id())
        if response.get("result") != "success":
            raise RuntimeError(f"Zulip API error: {response.get('msg')}")

    def _find_user_id_by_email(self, email: str) -> Optional[int]:
        users_response = self.client.get_users()
        if users_response.get("result") != "success":
            raise RuntimeError(f"Zulip API error: {users_response.get('msg')}")
        for member in users_response.get("members", []):
            if member.get("email") == email:
                user_id_value = member.get("user_id") or member.get("id")
                return int(user_id_value) if user_id_value is not None else None
        return None
