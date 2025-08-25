from domain.ports.chat_message_repository import ChatMessageRepository
from domain.entities.user import User
from domain.entities.chat_message import ChatMessage
from typing import List, Dict
import zulip
from infrastructure.config.zulip_config import ZulipConfig
from typing import Optional
from infrastructure.repositories.mappers.zulip_mapper import ZulipMapper
from domain.entities.channel import Channel

class ZulipChatMessageRepository(ChatMessageRepository):

    def __init__(self):
        self.config = ZulipConfig()
        self.client = zulip.Client(
            email=self.config.email,
            api_key=self.config.api_key,
            site=self.config.site,
        )
        self.mapper = ZulipMapper()

    def __group_messages_by_stream(self, messages: List[ChatMessage]) -> Dict[str, Channel]:
        # Group messages by stream using the raw message data
        channels = {}
        if hasattr(self, '_raw_messages'):
            for i, raw_msg in enumerate(self._raw_messages):
                stream_id = str(raw_msg.get("stream_id", ""))
                topic = raw_msg.get("subject", "")
                
                if stream_id not in channels:
                    channels[stream_id] = Channel(stream_id, topic, [], self)
                
                # Add the corresponding ChatMessage to the channel
                if i < len(messages):
                    channels[stream_id].add_message(messages[i])

        return channels

    def get_messages_from_channel(self, channel: Channel) -> List[ChatMessage]:
        messages = self.client.get_messages({
            "anchor": "newest",
            "num_before": 500,
            "num_after": 0,
            "narrow": [
                {"operator": "stream", "operand": channel.get_id()},
                {"operator": "topic", "operand": channel.get_topic()},
            ],
            "apply_markdown": True,
            "include_anchor": True,
            "include_history": True,
        })
        return [self.mapper.to_chat_message(msg) for msg in messages.get("messages", [])]

    def get_streams_with_unread_messages(self) -> Dict[str, Channel]:
        messages = self.get_unread_messages()
        channels = self.__group_messages_by_stream(messages)
        for channel in channels.values():
            messages = self.get_messages_from_channel(channel)
            for message in messages:
                channel.add_message(message)
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
            raise RuntimeError(f"Zulip API error: {response.get('msg')}")

        messages = response.get("messages", [])
        # Store the original messages for channel grouping
        self._raw_messages = messages
        return [self.mapper.to_chat_message(msg) for msg in messages]
    
    def send_private_message(self, message: str, user: User):
        if user.platform != "zulip":
            raise ValueError(f"User {user.platform_id} is not a Zulip user")
        recipient_user_id = self._find_user_id_by_email(user.platform_id)
        if recipient_user_id is None:
            raise ValueError(f"Recipient not found in Zulip realm for email: {user.platform_id}")

        request = {
            "type": "private",
            "to": [recipient_user_id],
            "content": message,
        }
        response = self.client.send_message(request)
        if response.get("result") != "success":
            raise RuntimeError(f"Zulip API error: {response.get('msg')}")

    def send_channel_message(self, message: str, channel_id: str, topic: str):
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
        response = self.client.mark_topic_as_read(channel.get_id(), channel.get_topic())
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