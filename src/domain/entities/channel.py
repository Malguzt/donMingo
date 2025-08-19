from typing import List, TYPE_CHECKING
from domain.entities.chat_message import ChatMessage

if TYPE_CHECKING:
    # Imported only for type checking to avoid circular import at runtime
    from domain.ports.chat_message_repository import ChatMessageRepository

class Channel:
    def __init__(self, id: str, topic: str, messages: List[ChatMessage], chat_message_repository: "ChatMessageRepository"):
        self.id = id
        self.topic = topic
        self.messages = messages
        self.chat_message_repository = chat_message_repository

    def __eq__(self, other) -> bool:
        return self.id == other.id and self.topic == other.topic
    
    def __hash__(self) -> int:
        return hash((self.id, self.topic))
    
    def __str__(self) -> str:
        text = f"Channel topic: {self.topic} \n Messages:"
        for message in self.messages:
            text += f"\n------------\n {message}"
        return text
    
    def respond(self, message: str) -> None:
        self.chat_message_repository.send_channel_message(message, self.id, self.topic)
        self.chat_message_repository.mark_as_read(self)

    def get_last_message(self) -> ChatMessage:
        return self.messages[-1]

    def add_message(self, message: ChatMessage) -> None:
        self.messages.append(message)

    def get_messages(self) -> List[ChatMessage]:
        return self.messages
    
    def get_id(self) -> str:
        return self.id
    
    def get_topic(self) -> str:
        return self.topic