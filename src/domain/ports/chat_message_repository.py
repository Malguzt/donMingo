# Repository interface for chat messages

from abc import ABC, abstractmethod
from typing import List

from domain.entities.chat_message import ChatMessage
from domain.entities.user import User

class ChatMessageRepository(ABC):
    @abstractmethod
    def get_unread_messages(self, user: User) -> List[ChatMessage]:
        pass
    @abstractmethod
    def send_private_message(self, message: str, user: User):
        pass
    @abstractmethod
    def send_channel_message(self, message: str, channel_id: str):
        pass
    @abstractmethod
    def send_thread_message(self, message: str, thread_id: str):
        pass
    @abstractmethod
    def mark_as_read(self, message: ChatMessage):
        pass