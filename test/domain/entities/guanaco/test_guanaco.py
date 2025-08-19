import pytest
from unittest.mock import Mock
from domain.entities.guanaco.guanaco import Guanaco
from domain.entities.user import User
from domain.errors import MissingUserError, MissingRepositoryError
from domain.ports.chat_message_repository import ChatMessageRepository
from domain.entities.channel import Channel
from domain.ports.think_repository import ThinkRepository

class TestGuanaco:
    def test_should_raise_a_missing_user_error_when_try_to_work_without_a_user(self):
        guanaco = Guanaco()

        with pytest.raises(MissingUserError):
            guanaco.work()
    
    def test_should_raise_a_missing_repository_error_when_try_to_work_without_a_message_repository(self):
        guanaco = Guanaco(user=User(platform_id="1", platform="telegram", name="John Doe"))

        with pytest.raises(MissingRepositoryError):
            guanaco.work()
    
    def test_should_raise_a_missing_repository_error_when_try_to_work_without_a_think_repository(self):
        mock_chat_repo = Mock()
        guanaco = Guanaco(
            user=User(platform_id="1", platform="telegram", name="John Doe"), 
            chat_message_repository=mock_chat_repo
        )

        with pytest.raises(MissingRepositoryError):
            guanaco.work()

    def test_should_not_respond_when_the_last_sender_is_the_guanaco_user(self):
        mock_chat_repo = Mock(ChatMessageRepository)
        channel = Mock(Channel)
        user = Mock(User)
        channel.get_last_message.return_value = Mock(sender=user)
        mock_chat_repo.get_streams_with_unread_messages.return_value = {
            "1": channel
        }
        guanaco = Guanaco(
            user=user, 
            chat_message_repository=mock_chat_repo,
            think_repository=Mock(ThinkRepository)
        )

        result = guanaco.work()

        assert channel.respond.call_count == 0
        assert result is False
    
    def test_should_respond_to_the_channel_with_the_think_when_the_last_sender_is_not_the_guanaco_user(self):
        mock_chat_repo = Mock(ChatMessageRepository)
        mock_think_repo = Mock(ThinkRepository)
        mock_think_repo.get_think.return_value = "I think I'm a guanaco"
        channel = Mock(Channel)
        guanaco_user = Mock(User)
        last_sender = Mock(User)
        channel.get_last_message.return_value = Mock(sender=last_sender)
        mock_chat_repo.get_streams_with_unread_messages.return_value = {
            "1": channel
        }
        guanaco = Guanaco(
            user=guanaco_user, 
            chat_message_repository=mock_chat_repo,
            think_repository=mock_think_repo
        )

        result = guanaco.work()

        assert channel.respond.call_args[0][0] == "I think I'm a guanaco"
        assert result is True
    
    def test_should_return_false_when_no_work_is_available(self):
        mock_chat_repo = Mock(ChatMessageRepository)
        mock_think_repo = Mock(ThinkRepository)
        mock_think_repo.get_think.return_value = "I think I'm a guanaco"
        guanaco_user = Mock(User)
        mock_chat_repo.get_streams_with_unread_messages.return_value = {}
        guanaco = Guanaco(
            user=guanaco_user, 
            chat_message_repository=mock_chat_repo,
            think_repository=mock_think_repo
        )

        result = guanaco.work()

        assert result is False