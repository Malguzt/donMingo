from domain.entities.chat_message import ChatMessage
from domain.entities.user import User
import pytest
from datetime import datetime

# Fixed datetime for deterministic testing
FIXED_DATETIME = datetime(2024, 1, 1, 12, 0, 0)


class TestChatMessage:
    def test_should_create_a_chat_message(self):
        user = User(platform_id="1", platform="telegram", name="John Doe")
        chat_message = ChatMessage(
            id="1", 
            content="Hello, world!", 
            sender=user, 
            created_at=FIXED_DATETIME, 
        )
        assert chat_message.id == "1"
        assert chat_message.content == "Hello, world!"
        assert chat_message.sender.platform_id == "1"
        assert chat_message.sender.platform == "telegram"
        assert chat_message.sender.name == "John Doe"
    
    def test_should_fail_when_creating_a_chat_message_with_empty_id(self):
        user = User(platform_id="1", platform="telegram", name="John Doe")
        with pytest.raises(ValueError):
            ChatMessage(
                id="", 
                content="Hello, world!", 
                sender=user, 
                created_at=FIXED_DATETIME,
            )
    
    def test_should_fail_when_creating_a_chat_message_with_null_id(self):
        user = User(platform_id="1", platform="telegram", name="John Doe")
        with pytest.raises(ValueError):
            ChatMessage(
                id=None, 
                content="Hello, world!", 
                sender=user, 
                created_at=FIXED_DATETIME,
            )
    
    def test_should_fail_when_creating_a_chat_message_with_null_content(self):
        user = User(platform_id="1", platform="telegram", name="John Doe")
        with pytest.raises(ValueError):
            ChatMessage(
                id="1", 
                content=None, 
                sender=user, 
                created_at=FIXED_DATETIME,
            )
    
    def test_should_create_when_creating_a_chat_message_with_empty_content(self):
        user = User(platform_id="1", platform="telegram", name="John Doe")
        chat_message = ChatMessage(
            id="1", 
            content="", 
            sender=user, 
            created_at=FIXED_DATETIME, 
        )
        assert chat_message.content == ""
    
    def test_should_fail_when_creating_a_chat_message_with_null_sender(self):
        with pytest.raises(ValueError):
            ChatMessage(
                id="1", 
                content="Hello, world!", 
                sender=None, 
                created_at=FIXED_DATETIME,
            )

    def test_should_fail_when_creating_a_chat_message_with_null_created_at(self):
        user = User(platform_id="1", platform="telegram", name="John Doe")
        with pytest.raises(ValueError):
            ChatMessage(
                id="1", 
                content="Hello, world!", 
                sender=user, 
                created_at=None, 
            )
    
    def test_should_return_humman_readable_string_when_chat_message_is_converted_to_string(self):
        user = User(platform_id="1", platform="telegram", name="Juan Perez")
        chat_message = ChatMessage(
            id="1", 
            content="Hello, world!", 
            sender=user, 
            created_at=FIXED_DATETIME, 
        )
        assert str(chat_message) == "Message: Hello, world! \nSender: Juan Perez \nCreated at: 2024-01-01 12:00:00"
