from domain.entities.user import User

from datetime import datetime


class ChatMessage:
    def __init__(self, id: int, content: str, sender: User, created_at: datetime):
        if not id:
            raise ValueError("ID is required")
        if content is None:
            raise ValueError("Content is required")
        if not sender:
            raise ValueError("Sender is required")
        if not created_at:
            raise ValueError("Created at is required")
        
        self.id = id
        self.content = content
        self.sender = sender
        self.created_at = created_at
    
    def __str__(self):
        return f"Message: {self.content} \nSender: {self.sender.name} \nCreated at: {self.created_at}"