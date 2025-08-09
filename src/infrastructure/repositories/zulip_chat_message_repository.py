from domain.ports.chat_message_repository import ChatMessageRepository
from domain.entities.user import User
from domain.entities.chat_message import ChatMessage
from typing import List
import zulip
from infrastructure.config.zulip_config import ZulipConfig
from datetime import datetime
from typing import Optional
from infrastructure.repositories.mappers.zulip_mapper import ZulipMapper

class ZulipChatMessageRepository(ChatMessageRepository):

    def __init__(self):
        self.config = ZulipConfig()
        self.client = zulip.Client(
            email=self.config.email,
            api_key=self.config.api_key,
            site=self.config.site,
        )
        self.mapper = ZulipMapper()
    def get_unread_messages(self, user: User) -> List[ChatMessage]:
        params = {
            "anchor": "newest",
            "use_first_unread_anchor": True,
            "num_before": 50,
            "num_after": 0,
            "narrow": [
                {"operator": "is", "operand": "unread"},
            ],
            "apply_markdown": True,
        }

        response = self.client.get_messages(params)
        if response.get("result") != "success":
            raise RuntimeError(f"Zulip API error: {response.get('msg')}")

        messages = response.get("messages", [])
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

    def send_channel_message(self, message: str, channel_id: str):
        request = {
            "type": "stream",
            "to": channel_id,
            "content": message,
        }
        response = self.client.send_message(request)
        if response.get("result") != "success":
            raise RuntimeError(f"Zulip API error: {response.get('msg')}")

    def send_thread_message(self, message: str, thread_id: str):
        request = {
            "type": "stream",
            "to": thread_id,
            "content": message,
        }
        response = self.client.send_message(request)
        if response.get("result") != "success":
            raise RuntimeError(f"Zulip API error: {response.get('msg')}")

    def mark_as_read(self, message: ChatMessage):
        self.client.mark_message_as_read(message.id)

    def _find_user_id_by_email(self, email: str) -> Optional[int]:
        users_response = self.client.get_users()
        if users_response.get("result") != "success":
            raise RuntimeError(f"Zulip API error: {users_response.get('msg')}")
        for member in users_response.get("members", []):
            if member.get("email") == email:
                user_id_value = member.get("user_id") or member.get("id")
                return int(user_id_value) if user_id_value is not None else None
        return None