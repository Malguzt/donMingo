import pytest
from src.domain.ports.chat_message_repository import ChatMessageRepository
from src.domain.entities.user import User
from src.domain.entities.channel import Channel

class TestChatMessageRepository:
    @classmethod
    def setup_class(cls):
        """Setup method to create base DummyRepo class once for all tests"""
        class BaseDummyRepo(ChatMessageRepository):
            def get_unread_messages(self, user: User):
                raise NotImplementedError()
            def send_private_message(self, message: str, user: User):
                raise NotImplementedError()
            def send_channel_message(self, message: str, channel_id: str, topic: str):
                raise NotImplementedError()
            def send_thread_message(self, message: str, thread_id: str, topic: str):
                raise NotImplementedError()
            def mark_as_read(self, channel: Channel):
                raise NotImplementedError()
            def get_streams_with_unread_messages(self):
                raise NotImplementedError()
        
        cls.BaseDummyRepo = BaseDummyRepo
    
    def test_should_rais_not_implemented_error_when_calling_get_unread_messages(self):
        repository = self.BaseDummyRepo()
        user = User(platform_id="1", platform="test", name="Test User")
        with pytest.raises(NotImplementedError):
            repository.get_unread_messages(user)
    
    def test_should_rais_not_implemented_error_when_calling_send_private_message(self):
        repository = self.BaseDummyRepo()
        user = User(platform_id="1", platform="test", name="Test User")
        with pytest.raises(NotImplementedError):
            repository.send_private_message("test", user)
    
    def test_should_rais_not_implemented_error_when_calling_send_channel_message(self):
        repository = self.BaseDummyRepo()
        with pytest.raises(NotImplementedError):
            repository.send_channel_message("test", "1", "topic")
    
    def test_should_rais_not_implemented_error_when_calling_send_thread_message(self):
        repository = self.BaseDummyRepo()
        with pytest.raises(NotImplementedError):
            repository.send_thread_message("test", "1", "topic")
    
    def test_should_rais_not_implemented_error_when_calling_mark_as_read(self):
        repository = self.BaseDummyRepo()
        channel = Channel("test_channel", "test_stream", [], repository)
        with pytest.raises(NotImplementedError):
            repository.mark_as_read(channel)
    
    def test_should_rais_not_implemented_error_when_calling_get_streams_with_unread_messages(self):
        repository = self.BaseDummyRepo()
        with pytest.raises(NotImplementedError):
            repository.get_streams_with_unread_messages()