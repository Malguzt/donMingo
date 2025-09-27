from unittest.mock import Mock, patch
from infrastructure.repositories.mappers.zulip_mapper import ZulipMapper


class TestZulipMapper:
    @patch('infrastructure.repositories.mappers.zulip_mapper.ChatMessage')
    @patch('infrastructure.repositories.mappers.zulip_mapper.User')
    @patch('infrastructure.repositories.mappers.zulip_mapper.datetime')
    def test_should_map_zulip_message_to_chat_message(self, mock_datetime, mock_user, mock_chat_message):
        # Setup mocks
        mock_user = Mock()
        mock_user.return_value = mock_user
        
        mock_chat_message = Mock()
        mock_chat_message.return_value = mock_chat_message
        
        mock_datetime_instance = Mock()
        mock_datetime.fromtimestamp.return_value = mock_datetime_instance
        
        # Test data
        zulip_message = {
            "id": 12345,
            "content": "Hello, how are you?",
            "sender_id": 67890,
            "sender_full_name": "John Doe",
            "timestamp": 1609459200,  # 2021-01-01 00:00:00
            "stream_id": 42,
            "subject": "General Discussion"
        }
        
        mapper = ZulipMapper()
        result = mapper.to_chat_message(zulip_message)
        
        # Should create User with correct parameters
        mock_user.assert_called_once_with(
            platform_id=67890,
            platform="zulip",
            name="John Doe"
        )
        
        # Should convert timestamp to datetime
        mock_datetime.fromtimestamp.assert_called_once_with(1609459200)
        
        # Should create ChatMessage with correct parameters
        mock_chat_message.assert_called_once_with(
            id=12345,
            content="Hello, how are you?",
            sender=mock_user,
            created_at=mock_datetime_instance
        )
        
        # Should return the created chat message
    assert result == mock_chat_message
    @patch('infrastructure.repositories.mappers.zulip_mapper.ChatMessage')
    @patch('infrastructure.repositories.mappers.zulip_mapper.User')
    @patch('infrastructure.repositories.mappers.zulip_mapper.datetime')
    def test_should_handle_missing_fields_in_zulip_message(self, mock_datetime, mock_user, mock_chat_message):
        # Setup mocks
        mock_user = Mock()
        mock_user.return_value = mock_user
        
        mock_chat_message = Mock()
        mock_chat_message.return_value = mock_chat_message
        
        mock_datetime_instance = Mock()
        mock_datetime.fromtimestamp.return_value = mock_datetime_instance
        
        # Test data with missing fields (should use None values)
        zulip_message = {}
        
        mapper = ZulipMapper()
        result = mapper.to_chat_message(zulip_message)
        
        # Should create User with None values for missing fields
        mock_user.assert_called_once_with(
            platform_id=None,
            platform="zulip",
            name=None
        )
        
        # Should convert None timestamp to datetime
        mock_datetime.fromtimestamp.assert_called_once_with(None)
        
        # Should create ChatMessage with None values for missing fields
        mock_chat_message.assert_called_once_with(
            id=None,
            content=None,
            sender=mock_user,
            created_at=mock_datetime_instance
        )
        
        # Should return the created chat message
        assert result == mock_chat_message

