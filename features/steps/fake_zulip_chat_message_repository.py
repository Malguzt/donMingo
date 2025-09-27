from domain.ports.chat_message_repository import ChatMessageRepository
from domain.entities.user import User
from domain.entities.chat_message import ChatMessage
from typing import List, Dict
from domain.entities.channel import Channel

from datetime import datetime

class FakeZulipChatMessageRepository(ChatMessageRepository):
    def __init__(self):
        self.sent_messages = []
        self.read_topics = []

    def get_streams_with_unread_messages(self) -> Dict[str, Channel]:
        return {
            "1": Channel("1", "Test Topic", [ChatMessage("1", "Hello", User(platform_id="test user", platform="zulip"), datetime.now())], self),
            "2": Channel("2", "Another Topic", [ChatMessage("2", "Hello again", User(platform_id="test user", platform="zulip"), datetime.now())], self),
            "3": Channel("3", "Third Topic", [ChatMessage("3", "Hi there", User(platform_id="test user", platform="zulip"), datetime.now())], self),
        }

    def get_unread_messages(self) -> List[ChatMessage]:
        return [
            ChatMessage("1", "Hello", User(platform_id="test user", platform="zulip"), datetime.now()),
            ChatMessage("2", "Hello again", User(platform_id="test user", platform="zulip"), datetime.now()),
            ChatMessage("3", "Hi there", User(platform_id="test user", platform="zulip"), datetime.now()),
        ]

    def send_channel_message(self, message: str, channel_id: str, topic: str):
        print(f"Sending message: {message} to channel: {channel_id} topic: {topic}")
        self.sent_messages.append(ChatMessage(id=int(channel_id), content=message, sender=User(platform_id="test user", platform="zulip"), created_at=datetime.now()))

    def mark_as_read(self, channel: Channel):
        self.read_topics.append(channel.get_id())

    def send_private_message(self, message: str, user: User):
        pass

    def send_thread_message(self, message: str, thread_id: str, topic: str):
        pass
