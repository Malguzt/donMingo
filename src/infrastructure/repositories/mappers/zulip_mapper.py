from domain.entities.chat_message import ChatMessage
from domain.entities.user import User

class ZulipMapper:
    def to_chat_message(self, message: dict) -> ChatMessage:
        return ChatMessage(
            id=message.get("id"),
            content=message.get("content"),
            sender=User(id=message.get("sender_id"), name=message.get("sender_name"), email=message.get("sender_email")),
            receiver=User(id=message.get("receiver_id"), name=message.get("receiver_name"), email=message.get("receiver_email")),
            created_at=message.get("created_at"),
        )
    
    def to_user(self, message: dict) -> User:
        return User(
            id=message.get("sender_id"),
            name=message.get("sender_full_name"),
            email=message.get("sender_email"),
        )