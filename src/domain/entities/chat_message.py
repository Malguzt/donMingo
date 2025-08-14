from domain.entities.user import User

from datetime import datetime

class ChatMessage:
    def __init__(self, id: int, content: str, sender: User, created_at: datetime, channel: str, topic: str):
        self.id = id
        self.content = content
        self.sender = sender
        self.created_at = created_at
        self.channel = channel
        self.topic = topic
    
    def __str__(self):
        return f"Message: {self.content} \n Sender: {self.sender.name} \n Created at: {self.created_at}"