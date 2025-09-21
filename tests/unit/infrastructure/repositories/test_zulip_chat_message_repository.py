import pytest
from unittest.mock import Mock, patch
from infrastructure.repositories.zulip_chat_message_repository import ZulipChatMessageRepository


class TestZulipChatMessageRepository:
    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipMapper')
    @patch('infrastructure.repositories.zulip_chat_message_repository.zulip.Client')
    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipConfig')
    def test_should_initialize_with_zulip_client_and_mapper(self, mock_config, mock_client, mock_mapper):
        # Setup mocks
        mock_config = Mock()
        mock_config.email = "test@example.com"
        mock_config.api_key = "test_api_key"
        mock_config.site = "test.zulipchat.com"
        mock_config.return_value = mock_config
        
        mock_client = Mock()
        mock_client.return_value = mock_client
        
        mock_mapper = Mock()
        mock_mapper.return_value = mock_mapper
        
        repository = ZulipChatMessageRepository()
        
        # Should create config, client, and mapper
        mock_config.assert_called_once()
        mock_client.assert_called_once_with(
            email="test@example.com",
            api_key="test_api_key",
            site="test.zulipchat.com"
        )
        mock_mapper.assert_called_once()
        
        assert repository.config == mock_config
        assert repository.client == mock_client
        assert repository.mapper == mock_mapper

    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipMapper')
    @patch('infrastructure.repositories.zulip_chat_message_repository.zulip.Client')
    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipConfig')
    def test_should_get_unread_messages_successfully(self, mock_config, mock_client, mock_mapper):
        # Setup mocks
        self._setup_basic_mocks(mock_config, mock_client, mock_mapper)
        
        mock_client = mock_client.return_value
        mock_mapper = mock_mapper.return_value
        
        # Mock API response
        api_response = {
            "result": "success",
            "messages": [
                {"id": 1, "content": "Hello"},
                {"id": 2, "content": "World"}
            ]
        }
        mock_client.get_messages.return_value = api_response
        
        # Mock mapper responses
        mock_message1 = Mock()
        mock_message2 = Mock()
        mock_mapper.to_chat_message.side_effect = [mock_message1, mock_message2]
        
        repository = ZulipChatMessageRepository()
        result = repository.get_unread_messages()
        
        # Should call API with correct parameters
        expected_params = {
            "anchor": "first_unread",
            "num_before": 0,
            "num_after": 200,
            "use_first_unread_anchor": True,
            "narrow": [{"operator": "is", "operand": "unread"}],
            "apply_markdown": True,
            "include_anchor": True,
            "include_history": True,
        }
        mock_client.get_messages.assert_called_once_with(expected_params)
        
        # Should map all messages
        assert mock_mapper.to_chat_message.call_count == 2
        mock_mapper.to_chat_message.assert_any_call({"id": 1, "content": "Hello"})
        mock_mapper.to_chat_message.assert_any_call({"id": 2, "content": "World"})
        
        assert result == [mock_message1, mock_message2]

    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipMapper')
    @patch('infrastructure.repositories.zulip_chat_message_repository.zulip.Client')
    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipConfig')
    def test_should_raise_error_on_api_failure_for_unread_messages(
        self, mock_config, mock_client, mock_mapper):
        # Setup mocks
        self._setup_basic_mocks(mock_config, mock_client, mock_mapper)
        
        mock_client = mock_client.return_value
        
        # Mock API error response
        api_response = {
            "result": "error",
            "msg": "Authentication failed"
        }
        mock_client.get_messages.return_value = api_response
        
        repository = ZulipChatMessageRepository()
        
        with pytest.raises(RuntimeError, match="Zulip API error: Authentication failed"):
            repository.get_unread_messages()

    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipMapper')
    @patch('infrastructure.repositories.zulip_chat_message_repository.zulip.Client')
    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipConfig')
    def test_should_get_messages_from_channel(self, mock_config, mock_client, mock_mapper):
        # Setup mocks
        self._setup_basic_mocks(mock_config, mock_client, mock_mapper)
        
        mock_client = mock_client.return_value
        mock_mapper = mock_mapper.return_value
        
        # Mock channel
        mock_channel = Mock()
        mock_channel.get_id.return_value = "42"
        mock_channel.get_topic.return_value = "General Discussion"
        
        # Mock API response
        api_response = {
            "messages": [
                {"id": 1, "content": "Channel message"}
            ]
        }
        mock_client.get_messages.return_value = api_response
        
        mock_message = Mock()
        mock_mapper.to_chat_message.return_value = mock_message
        
        repository = ZulipChatMessageRepository()
        result = repository.get_messages_from_channel(mock_channel)
        
        # Should call API with channel-specific parameters
        expected_params = {
            "anchor": "newest",
            "num_before": 500,
            "num_after": 0,
            "narrow": [
                {"operator": "stream", "operand": "42"},
                {"operator": "topic", "operand": "General Discussion"}
            ],
            "apply_markdown": True,
            "include_anchor": True,
            "include_history": True,
        }
        mock_client.get_messages.assert_called_once_with(expected_params)
        
        mock_mapper.to_chat_message.assert_called_once_with({"id": 1, "content": "Channel message"})
        assert result == [mock_message]

    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipMapper')
    @patch('infrastructure.repositories.zulip_chat_message_repository.zulip.Client')
    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipConfig')
    def test_should_send_private_message_successfully(self, mock_config, mock_client, mock_mapper):
        # Setup mocks
        self._setup_basic_mocks(mock_config, mock_client, mock_mapper)
        
        mock_client = mock_client.return_value
        
        # Mock user lookup
        users_response = {
            "result": "success",
            "members": [
                {"email": "john@example.com", "user_id": 123},
                {"email": "jane@example.com", "user_id": 456}
            ]
        }
        mock_client.get_users.return_value = users_response
        
        # Mock send message success
        send_response = {"result": "success"}
        mock_client.send_message.return_value = send_response
        
        # Test user
        user = Mock()
        user.email = "john@example.com"
        
        repository = ZulipChatMessageRepository()
        repository.send_private_message("Hello John!", user)
        
        # Should look up user
        mock_client.get_users.assert_called_once()
        
        # Should send message
        expected_request = {
            "type": "private",
            "to": [123],
            "content": "Hello John!"
        }
        mock_client.send_message.assert_called_once_with(expected_request)

    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipMapper')
    @patch('infrastructure.repositories.zulip_chat_message_repository.zulip.Client')
    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipConfig')
    def test_should_raise_error_when_user_not_found_for_private_message(
        self, mock_config, mock_client, mock_mapper):
        # Setup mocks
        self._setup_basic_mocks(mock_config, mock_client, mock_mapper)
        
        mock_client = mock_client.return_value
        
        # Mock user lookup with no matching user
        users_response = {
            "result": "success",
            "members": [
                {"email": "other@example.com", "user_id": 999}
            ]
        }
        mock_client.get_users.return_value = users_response
        
        user = Mock()
        user.email = "notfound@example.com"
        
        repository = ZulipChatMessageRepository()
        
        with pytest.raises(ValueError, match="Recipient not found in Zulip realm for email: notfound@example.com"):
            repository.send_private_message("Hello!", user)

    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipMapper')
    @patch('infrastructure.repositories.zulip_chat_message_repository.zulip.Client')
    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipConfig')
    def test_should_send_channel_message_successfully(self, mock_config, mock_client, mock_mapper):
        # Setup mocks
        self._setup_basic_mocks(mock_config, mock_client, mock_mapper)
        
        mock_client = mock_client.return_value
        
        # Mock send message success
        send_response = {"result": "success"}
        mock_client.send_message.return_value = send_response
        
        repository = ZulipChatMessageRepository()
        repository.send_channel_message("Hello channel!", "general", "Discussion")
        
        # Should send message with correct parameters
        expected_request = {
            "type": "stream",
            "to": "general",
            "content": "Hello channel!",
            "subject": "Discussion"
        }
        mock_client.send_message.assert_called_once_with(expected_request)

    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipMapper')
    @patch('infrastructure.repositories.zulip_chat_message_repository.zulip.Client')
    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipConfig')
    def test_should_send_thread_message_successfully(self, mock_config, mock_client, mock_mapper):
        # Setup mocks
        self._setup_basic_mocks(mock_config, mock_client, mock_mapper)
        
        mock_client = mock_client.return_value
        
        # Mock send message success
        send_response = {"result": "success"}
        mock_client.send_message.return_value = send_response
        
        repository = ZulipChatMessageRepository()
        repository.send_thread_message("Hello thread!", "123", "Discussion")
        
        # Should send message with correct parameters
        expected_request = {
            "type": "stream",
            "to": "123",
            "content": "Hello thread!",
            "subject": "Discussion"
        }
        mock_client.send_message.assert_called_once_with(expected_request)

    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipMapper')
    @patch('infrastructure.repositories.zulip_chat_message_repository.zulip.Client')
    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipConfig')
    def test_should_mark_channel_as_read(self, mock_config, mock_client, mock_mapper):
        # Setup mocks
        self._setup_basic_mocks(mock_config, mock_client, mock_mapper)
        
        mock_client = mock_client.return_value
        
        # Mock mark as read success
        mark_response = {"result": "success"}
        mock_client.mark_stream_as_read.return_value = mark_response
        
        # Mock channel
        mock_channel = Mock()
        mock_channel.get_id.return_value = "42"
        
        repository = ZulipChatMessageRepository()
        repository.mark_as_read(mock_channel)
        
        # Should mark stream as read
        mock_client.mark_stream_as_read.assert_called_once_with("42")

    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipMapper')
    @patch('infrastructure.repositories.zulip_chat_message_repository.zulip.Client')
    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipConfig')
    def test_should_raise_error_on_mark_as_read_failure(self, mock_config, mock_client, mock_mapper):
        # Setup mocks
        self._setup_basic_mocks(mock_config, mock_client, mock_mapper)
        
        mock_client = mock_client.return_value
        
        # Mock mark as read failure
        mark_response = {"result": "error", "msg": "Stream not found"}
        mock_client.mark_stream_as_read.return_value = mark_response
        
        mock_channel = Mock()
        mock_channel.get_id.return_value = "invalid"
        
        repository = ZulipChatMessageRepository()
        
        with pytest.raises(RuntimeError, match="Zulip API error: Stream not found"):
            repository.mark_as_read(mock_channel)

    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipMapper')
    @patch('infrastructure.repositories.zulip_chat_message_repository.zulip.Client')
    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipConfig')
    def test_should_find_user_id_by_email_with_user_id_field(
        self, mock_config, mock_client, mock_mapper):
        # Setup mocks
        self._setup_basic_mocks(mock_config, mock_client, mock_mapper)
        
        mock_client = mock_client.return_value
        
        # Mock user lookup
        users_response = {
            "result": "success",
            "members": [
                {"email": "test@example.com", "user_id": 42}
            ]
        }
        mock_client.get_users.return_value = users_response
        
        repository = ZulipChatMessageRepository()
        result = repository._find_user_id_by_email("test@example.com")
        
        assert result == 42

    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipMapper')
    @patch('infrastructure.repositories.zulip_chat_message_repository.zulip.Client')
    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipConfig')
    def test_should_find_user_id_by_email_with_id_field(self, mock_config, mock_client, mock_mapper):
        # Setup mocks
        self._setup_basic_mocks(mock_config, mock_client, mock_mapper)
        
        mock_client = mock_client.return_value
        
        # Mock user lookup with 'id' field instead of 'user_id'
        users_response = {
            "result": "success",
            "members": [
                {"email": "test@example.com", "id": 123}
            ]
        }
        mock_client.get_users.return_value = users_response
        
        repository = ZulipChatMessageRepository()
        result = repository._find_user_id_by_email("test@example.com")
        
        assert result == 123

    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipMapper')
    @patch('infrastructure.repositories.zulip_chat_message_repository.zulip.Client')
    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipConfig')
    def test_should_return_none_when_user_not_found(self, mock_config, mock_client, mock_mapper):
        # Setup mocks
        self._setup_basic_mocks(mock_config, mock_client, mock_mapper)
        
        mock_client = mock_client.return_value
        
        # Mock user lookup with no matching user
        users_response = {
            "result": "success",
            "members": [
                {"email": "other@example.com", "user_id": 999}
            ]
        }
        mock_client.get_users.return_value = users_response
        
        repository = ZulipChatMessageRepository()
        result = repository._find_user_id_by_email("notfound@example.com")
        
        assert result is None

    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipMapper')
    @patch('infrastructure.repositories.zulip_chat_message_repository.zulip.Client')
    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipConfig')
    def test_should_raise_error_on_get_users_failure(self, mock_config, mock_client, mock_mapper):
        # Setup mocks
        self._setup_basic_mocks(mock_config, mock_client, mock_mapper)
        
        mock_client = mock_client.return_value
        
        # Mock get users failure
        users_response = {
            "result": "error",
            "msg": "Permission denied"
        }
        mock_client.get_users.return_value = users_response
        
        repository = ZulipChatMessageRepository()
        
        with pytest.raises(RuntimeError, match="Zulip API error: Permission denied"):
            repository._find_user_id_by_email("test@example.com")

    @patch('infrastructure.repositories.zulip_chat_message_repository.Channel')
    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipMapper')
    @patch('infrastructure.repositories.zulip_chat_message_repository.zulip.Client')
    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipConfig')
    def test_should_get_streams_with_unread_messages(
        self, mock_config, mock_client, mock_mapper, mock_channel_class
    ):
        # Setup mocks
        self._setup_basic_mocks(mock_config, mock_client, mock_mapper)
        
        mock_client = mock_client.return_value
        mock_mapper = mock_mapper.return_value
        
        # Mock raw messages (what comes from Zulip API)
        raw_messages = [
            {"stream_id": "42", "subject": "Discussion", "id": 1, "content": "Hello"},
            {"stream_id": "43", "subject": "Chat", "id": 2, "content": "World"}
        ]
        
        # Mock unread messages response
        unread_response = {
            "result": "success",
            "messages": raw_messages
        }
        mock_client.get_messages.return_value = unread_response
        
        # Mock ChatMessage objects
        mock_message1 = Mock()
        mock_message2 = Mock()
        mock_mapper.to_chat_message.side_effect = [mock_message1, mock_message2]
        
        # Mock channel creation
        mock_channel1 = Mock()
        mock_channel2 = Mock()
        mock_channel_class.side_effect = [mock_channel1, mock_channel2]
        
        # Mock get_messages_from_channel to return additional messages
        mock_channel_msg1 = Mock()
        mock_channel_msg2 = Mock()
        
        repository = ZulipChatMessageRepository()
        
        with patch.object(repository, 'get_messages_from_channel') as mock_get_channel_msgs:
            mock_get_channel_msgs.side_effect = [[mock_channel_msg1], [mock_channel_msg2]]
            
            result = repository.get_streams_with_unread_messages()
            
            # Should create channels for each unique stream
            assert mock_channel_class.call_count == 2
            mock_channel_class.assert_any_call("42", "Discussion", [], repository)
            mock_channel_class.assert_any_call("43", "Chat", [], repository)
            
            # Should add unread messages to channels
            mock_channel1.add_message.assert_any_call(mock_message1)
            mock_channel2.add_message.assert_any_call(mock_message2)
            
            # Should get additional messages from each channel
            mock_get_channel_msgs.assert_any_call(mock_channel1)
            mock_get_channel_msgs.assert_any_call(mock_channel2)
            
            # Should add channel messages
            mock_channel1.add_message.assert_any_call(mock_channel_msg1)
            mock_channel2.add_message.assert_any_call(mock_channel_msg2)
            
            # Should return channels by stream ID
            assert "42" in result
            assert "43" in result
            assert result["42"] == mock_channel1
            assert result["43"] == mock_channel2

    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipMapper')
    @patch('infrastructure.repositories.zulip_chat_message_repository.zulip.Client')
    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipConfig')
    def test_should_raise_error_on_send_private_message_failure(self, mock_config, mock_client, mock_mapper):
        # Setup mocks
        self._setup_basic_mocks(mock_config, mock_client, mock_mapper)
        
        mock_client = mock_client.return_value
        
        # Mock user lookup success
        users_response = {"result": "success", "members": [{"email": "test@example.com", "user_id": 123}]}
        mock_client.get_users.return_value = users_response
        
        # Mock send message failure
        send_response = {"result": "error", "msg": "Message sending failed"}
        mock_client.send_message.return_value = send_response
        
        user = Mock()
        user.email = "test@example.com"
        
        repository = ZulipChatMessageRepository()
        
        with pytest.raises(RuntimeError, match="Zulip API error: Message sending failed"):
            repository.send_private_message("Hello!", user)

    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipMapper')
    @patch('infrastructure.repositories.zulip_chat_message_repository.zulip.Client')
    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipConfig')
    def test_should_raise_error_on_send_channel_message_failure(self, mock_config, mock_client, mock_mapper):
        # Setup mocks
        self._setup_basic_mocks(mock_config, mock_client, mock_mapper)
        
        mock_client = mock_client.return_value
        
        # Mock send message failure
        send_response = {"result": "error", "msg": "Channel not found"}
        mock_client.send_message.return_value = send_response
        
        repository = ZulipChatMessageRepository()
        
        with pytest.raises(RuntimeError, match="Zulip API error: Channel not found"):
            repository.send_channel_message("Hello!", "nonexistent", "Topic")

    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipMapper')
    @patch('infrastructure.repositories.zulip_chat_message_repository.zulip.Client')
    @patch('infrastructure.repositories.zulip_chat_message_repository.ZulipConfig')
    def test_should_raise_error_on_send_thread_message_failure(self, mock_config, mock_client, mock_mapper):
        # Setup mocks
        self._setup_basic_mocks(mock_config, mock_client, mock_mapper)
        
        mock_client = mock_client.return_value
        
        # Mock send message failure
        send_response = {"result": "error", "msg": "Thread not found"}
        mock_client.send_message.return_value = send_response
        
        repository = ZulipChatMessageRepository()
        
        with pytest.raises(RuntimeError, match="Zulip API error: Thread not found"):
            repository.send_thread_message("Hello!", "nonexistent", "Topic")

    def _setup_basic_mocks(self, mock_config, mock_client, mock_mapper):
        """Helper method to set up basic mocks for most tests"""
        mock_config = Mock()
        mock_config.email = "test@example.com"
        mock_config.api_key = "test_key"
        mock_config.site = "test.zulipchat.com"
        mock_config.return_value = mock_config
        
        mock_client = Mock()
        mock_client.return_value = mock_client
        
        mock_mapper = Mock()
        mock_mapper.return_value = mock_mapper
