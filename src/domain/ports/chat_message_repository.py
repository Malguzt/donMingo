# Repository interface for chat messages

from abc import ABC, abstractmethod
from typing import List, Dict

from domain.entities.chat_message import ChatMessage
from domain.entities.user import User
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities.channel import Channel

class ChatMessageRepository(ABC):
    @abstractmethod
    def get_unread_messages(self, user: User) -> List[ChatMessage]:
        raise NotImplementedError("Not implemented")
    @abstractmethod
    def send_private_message(self, message: str, user: User):
        raise NotImplementedError("Not implemented")
    @abstractmethod
    def send_channel_message(self, message: str, channel_id: str, topic: str):
        raise NotImplementedError("Not implemented")
    @abstractmethod
    def send_thread_message(self, message: str, thread_id: str, topic: str):
        raise NotImplementedError("Not implemented")
    @abstractmethod
    def mark_as_read(self, channel: "Channel"):
        raise NotImplementedError("Not implemented")
    @abstractmethod
    def get_streams_with_unread_messages(self) -> Dict[str, "Channel"]:
        raise NotImplementedError("Not implemented")