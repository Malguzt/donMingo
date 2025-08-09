from domain.entities.user import User

from datetime import datetime

class ChatMessage:
    def __init__(self, id: int, content: str, sender: User, receiver: User, created_at: datetime):
        self.id = id
        self.content = content
        self.sender = sender
        self.receiver = receiver
        self.created_at = created_at