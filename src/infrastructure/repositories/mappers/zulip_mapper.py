from domain.entities.chat_message import ChatMessage
from domain.entities.user import User
import json
from datetime import datetime

class ZulipMapper:
    def to_chat_message(self, message: dict) -> ChatMessage:
        return ChatMessage(
            id=message.get("id"),
            content=message.get("content"),
            sender=User(platform_id=message.get("sender_id"), platform="zulip", name=message.get("sender_full_name")),
            created_at= datetime.fromtimestamp(message.get("timestamp")),
            channel=message.get("stream_id"),
            topic=message.get("subject"),
        )