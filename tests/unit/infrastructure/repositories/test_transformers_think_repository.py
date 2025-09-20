import pytest
from unittest.mock import Mock, patch
from infrastructure.repositories.transformers_think_repository import TransformersThinkRepository


class TestTransformersThinkRepository:
    @patch('infrastructure.repositories.transformers_think_repository.ModelsHandler')
    def test_should_initialize_with_models_handler(self, mock_models_handler_class):
        mock_handler = Mock()
        mock_models_handler_class.return_value = mock_handler
        
        repository = TransformersThinkRepository()
        
        # Should initialize ModelsHandler
        mock_models_handler_class.assert_called_once()
        assert repository.transformers_engine == mock_handler

    @patch('infrastructure.repositories.transformers_think_repository.ModelsHandler')
    def test_should_return_generated_text_from_models_handler(self, mock_models_handler_class):
        mock_handler = Mock()
        mock_handler.generate_text.return_value = "This is a generated response from the model"
        mock_models_handler_class.return_value = mock_handler
        
        repository = TransformersThinkRepository()
        response = repository.get_think("What do you think about AI?")
        
        # Should call the models handler with the message
        mock_handler.generate_text.assert_called_once_with("What do you think about AI?")
        # Should return the exact literal response from the handler
        assert response == "This is a generated response from the model"

    @patch('infrastructure.repositories.transformers_think_repository.ModelsHandler')
    def test_should_handle_empty_message(self, mock_models_handler_class):
        mock_handler = Mock()
        mock_handler.generate_text.return_value = "Empty input received"
        mock_models_handler_class.return_value = mock_handler
        
        repository = TransformersThinkRepository()
        response = repository.get_think("")
        
        # Should call the models handler with empty string
        mock_handler.generate_text.assert_called_once_with("")
        # Should return the exact literal response
        assert response == "Empty input received"

    @patch('infrastructure.repositories.transformers_think_repository.ModelsHandler')
    def test_should_propagate_exception_from_models_handler(self, mock_models_handler_class):
        mock_handler = Mock()
        mock_handler.generate_text.side_effect = Exception("Model loading failed")
        mock_models_handler_class.return_value = mock_handler
        
        repository = TransformersThinkRepository()
        
        # Should propagate the exception from the models handler
        with pytest.raises(Exception, match="Model loading failed"):
            repository.get_think("test message")
