from domain.entities.chat_message import ChatMessage
from domain.entities.user import User
from datetime import datetime


class ZulipMapper:
    def to_chat_message(self, message: dict) -> ChatMessage:
        sender_platform_id = message.get("sender_id")
        print(f"[DEBUG] ZulipMapper: Mapping sender with platform_id: {sender_platform_id}")
        return ChatMessage(
            id=message.get("id"),
            content=message.get("content"),
            sender=User(
                platform_id=sender_platform_id, 
                platform="zulip", 
                name=message.get("sender_full_name")
            ),
            created_at=datetime.fromtimestamp(message.get("timestamp")),
        )
