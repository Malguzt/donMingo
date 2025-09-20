from domain.entities.channel import Channel
from unittest.mock import Mock
from domain.ports.chat_message_repository import ChatMessageRepository

class TestChannel:
    def test_should_define_channel_as_equal_when_id_and_topic_are_the_same(self):
        # Create mock dependencies
        mock_repository = Mock(spec=ChatMessageRepository)
        empty_messages = []
        
        channel_1 = Channel(id="1", topic="Test Topic", messages=empty_messages, chat_message_repository=mock_repository)
        channel_2 = Channel(id="1", topic="Test Topic", messages=empty_messages, chat_message_repository=mock_repository)
        
        assert channel_1 == channel_2
    
    def test_should_define_channel_as_not_equal_when_id_is_different(self):
        mock_repository = Mock(spec=ChatMessageRepository)
        empty_messages = []
        
        channel_1 = Channel(id="1", topic="Test Topic", messages=empty_messages, chat_message_repository=mock_repository)
        channel_2 = Channel(id="2", topic="Test Topic", messages=empty_messages, chat_message_repository=mock_repository)
        
        assert channel_1 != channel_2
    
    def test_should_define_channel_as_not_equal_when_topic_is_different(self):
        mock_repository = Mock(spec=ChatMessageRepository)
        empty_messages = []
        
        channel_1 = Channel(id="1", topic="Test Topic", messages=empty_messages, chat_message_repository=mock_repository)
        channel_2 = Channel(id="1", topic="Different Topic", messages=empty_messages, chat_message_repository=mock_repository)
        
        assert channel_1 != channel_2
    
    def test_should_make_different_hash_for_different_id(self):
        mock_repository = Mock(spec=ChatMessageRepository)
        empty_messages = []
        
        channel_1 = Channel(id="1", topic="Test Topic", messages=empty_messages, chat_message_repository=mock_repository)
        channel_2 = Channel(id="2", topic="Test Topic", messages=empty_messages, chat_message_repository=mock_repository)
        
        assert hash(channel_1) != hash(channel_2)
    
    def test_should_make_different_hash_for_different_topic(self):
        mock_repository = Mock(spec=ChatMessageRepository)
        empty_messages = []
        
        channel_1 = Channel(id="1", topic="Test Topic", messages=empty_messages, chat_message_repository=mock_repository)
        channel_2 = Channel(id="1", topic="Different Topic", messages=empty_messages, chat_message_repository=mock_repository)
        
        assert hash(channel_1) != hash(channel_2)
    
    def test_should_make_same_hash_for_same_id_and_topic(self):
        mock_repository = Mock(spec=ChatMessageRepository)
        empty_messages = []
        
        channel_1 = Channel(id="1", topic="Test Topic", messages=empty_messages, chat_message_repository=mock_repository)
        channel_2 = Channel(id="1", topic="Test Topic", messages=empty_messages, chat_message_repository=mock_repository)
        
        assert hash(channel_1) == hash(channel_2)
    
    def test_should_add_message_to_channel(self):
        mock_repository = Mock(spec=ChatMessageRepository)
        empty_messages = []
        mock_message = Mock()
        
        channel = Channel(id="1", topic="Test Topic", messages=empty_messages, chat_message_repository=mock_repository)
        channel.add_message(mock_message)
        
        assert len(channel.get_messages()) == 1
        assert channel.get_messages()[0] == mock_message
    
    def test_should_get_last_message(self):
        mock_repository = Mock(spec=ChatMessageRepository)
        mock_message_1 = Mock()
        mock_message_2 = Mock()
        messages = [mock_message_1, mock_message_2]
        
        channel = Channel(id="1", topic="Test Topic", messages=messages, chat_message_repository=mock_repository)
        
        assert channel.get_last_message() == mock_message_2
    
    def test_should_get_channel_id(self):
        mock_repository = Mock(spec=ChatMessageRepository)
        empty_messages = []
        
        channel = Channel(id="test_id", topic="Test Topic", messages=empty_messages, chat_message_repository=mock_repository)
        
        assert channel.get_id() == "test_id"
    
    def test_should_get_channel_topic(self):
        mock_repository = Mock(spec=ChatMessageRepository)
        empty_messages = []
        
        channel = Channel(id="1", topic="Test Topic", messages=empty_messages, chat_message_repository=mock_repository)
        
        assert channel.get_topic() == "Test Topic"
    
    def test_should_use_the_topic_in_the_string_representation(self):
        mock_repository = Mock(spec=ChatMessageRepository)
        empty_messages = []
        
        channel = Channel(id="1", topic="Test Topic", messages=empty_messages, chat_message_repository=mock_repository)
        
        assert str(channel) == "Channel topic: Test Topic \n Messages:"
    
    def test_should_put_not_message_when_there_are_no_messages(self):
        mock_repository = Mock(spec=ChatMessageRepository)
        empty_messages = []
        
        channel = Channel(id="1", topic="Test Topic", messages=empty_messages, chat_message_repository=mock_repository)
        
        assert str(channel) == "Channel topic: Test Topic \n Messages:"
    
    def test_should_put_one_message_when_there_is_one(self):
        mock_repository = Mock(spec=ChatMessageRepository)
        mock_message = Mock()
        messages = [mock_message]
        mock_message.__str__ = Mock(return_value="Test Message 1")
        
        channel = Channel(id="1", topic="Test Topic", messages=messages, chat_message_repository=mock_repository)
        
        assert str(channel) == "Channel topic: Test Topic \n Messages:\n------------\n Test Message 1"
    
    def test_should_put_two_messages_when_there_are_two(self):
        mock_repository = Mock(spec=ChatMessageRepository)
        mock_message_1 = Mock()
        mock_message_2 = Mock()
        messages = [mock_message_1, mock_message_2]
        mock_message_1.__str__ = Mock(return_value="Test Message 1")
        mock_message_2.__str__ = Mock(return_value="Test Message 2")
        
        channel = Channel(id="1", topic="Test Topic", messages=messages, chat_message_repository=mock_repository)
        
        assert str(channel) == "Channel topic: Test Topic \n Messages:\n------------\n Test Message 1\n------------\n Test Message 2"
    
    def test_should_send_response_to_the_chat_message_repository(self):
        mock_chat_message_repository = Mock(spec=ChatMessageRepository)
        
        channel = Channel(id="1", topic="Test Topic", messages=[], chat_message_repository=mock_chat_message_repository)
        channel.respond("Test Message")
         
        mock_chat_message_repository.send_channel_message.assert_called_once_with("Test Message", "1", "Test Topic")

    def test_should_mark_channel_as_read_when_respond(self):
        mock_repository = Mock(spec=ChatMessageRepository)
        empty_messages = []
        
        channel = Channel(id="1", topic="Test Topic", messages=empty_messages, chat_message_repository=mock_repository)
        channel.respond("Test Message")
        
        mock_repository.mark_as_read.assert_called_once_with(channel)
        