from unittest.mock import Mock, patch
from infrastructure.repositories.local_guanacos_repository import LocalGuanacosRepository


class TestLocalGuanacosRepository:
    @patch('infrastructure.repositories.local_guanacos_repository.TransformersThinkRepository')
    @patch('infrastructure.repositories.local_guanacos_repository.ZulipChatMessageRepository')
    @patch('infrastructure.repositories.local_guanacos_repository.User')
    @patch('infrastructure.repositories.local_guanacos_repository.Guanaco')
    def test_should_return_list_of_guanacos_with_mocked_dependencies(self, mock_guanaco_class, mock_user_class, mock_zulip_repo_class, mock_transformers_repo_class):
        # Setup mocks
        mock_user = Mock()
        mock_user_class.return_value = mock_user
        
        mock_zulip_repo = Mock()
        mock_zulip_repo_class.return_value = mock_zulip_repo
        
        mock_transformers_repo = Mock()
        mock_transformers_repo_class.return_value = mock_transformers_repo
        
        mock_guanaco = Mock()
        mock_guanaco_class.return_value = mock_guanaco
        
        repository = LocalGuanacosRepository()
        guanacos = repository.get_guanacos()
        
        # Should create User with correct parameters
        mock_user_class.assert_called_once_with(
            platform_id=1,
            platform="zulip", 
            name="Paco"
        )
        
        # Should create repositories
        mock_zulip_repo_class.assert_called_once()
        mock_transformers_repo_class.assert_called_once()
        
        # Should create Guanaco with correct parameters
        mock_guanaco_class.assert_called_once_with(
            name="Pancho",
            user=mock_user,
            chat_message_repository=mock_zulip_repo,
            think_repository=mock_transformers_repo
        )
        
        # Should return a list with one guanaco
        assert guanacos == [mock_guanaco]
        assert len(guanacos) == 1
