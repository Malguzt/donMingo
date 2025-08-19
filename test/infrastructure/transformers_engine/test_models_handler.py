import pytest
from unittest.mock import Mock, patch, MagicMock
from infrastructure.transformers_engine.models_handler import ModelsHandler


class TestModelsHandler:
    @patch('infrastructure.transformers_engine.models_handler.torch')
    @patch('infrastructure.transformers_engine.models_handler.os')
    def test_should_initialize_with_device_listing(self, mock_os, mock_torch):
        # Setup mocks for device availability
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 2
        mock_os.cpu_count.return_value = 8
        mock_torch.backends.mps.is_available.return_value = False
        
        # Mock XPU and ROCm availability
        mock_torch.xpu = Mock()
        mock_torch.xpu.is_available.return_value = False
        mock_torch.version.hip = None
        
        handler = ModelsHandler()
        
        # Should set models list
        assert handler.models == ["Qwen/Qwen3-1.7B"]
        assert handler._model is None
        assert handler._tokenizer is None
        
        # Should check device availability
        mock_torch.cuda.is_available.assert_called()
        mock_torch.cuda.device_count.assert_called()
        mock_os.cpu_count.assert_called()

    @patch('infrastructure.transformers_engine.models_handler.torch')
    @patch('infrastructure.transformers_engine.models_handler.os')
    def test_should_handle_missing_cpu_count(self, mock_os, mock_torch):
        # Setup mocks
        mock_torch.cuda.is_available.return_value = False
        mock_torch.cuda.device_count.return_value = 0
        mock_os.cpu_count.return_value = None  # This should default to 1
        
        handler = ModelsHandler()
        
        # Should handle None cpu_count gracefully
        mock_os.cpu_count.assert_called()

    @patch('infrastructure.transformers_engine.models_handler.AutoModelForCausalLM')
    @patch('infrastructure.transformers_engine.models_handler.torch')
    @patch('infrastructure.transformers_engine.models_handler.os')
    def test_should_get_model_with_device_map_auto(self, mock_os, mock_torch, mock_auto_model):
        # Setup mocks
        mock_torch.cuda.is_available.return_value = False
        mock_os.cpu_count.return_value = 4
        
        mock_model = Mock()
        mock_auto_model.from_pretrained.return_value = mock_model
        
        handler = ModelsHandler()
        result = handler.get_model("test-model")
        
        # Should load model with device_map="auto"
        mock_auto_model.from_pretrained.assert_called_once_with("test-model", device_map="auto")
        mock_model.eval.assert_called_once()
        assert result == mock_model
        assert handler._model == mock_model

    @patch('infrastructure.transformers_engine.models_handler.AutoModelForCausalLM')
    @patch('infrastructure.transformers_engine.models_handler.torch')
    @patch('infrastructure.transformers_engine.models_handler.os')
    def test_should_fallback_to_manual_device_placement_on_cuda(self, mock_os, mock_torch, mock_auto_model):
        # Setup mocks
        mock_torch.cuda.is_available.return_value = True
        mock_os.cpu_count.return_value = 4
        
        mock_model = Mock()
        # First call raises exception, second succeeds
        mock_auto_model.from_pretrained.side_effect = [Exception("Device map failed"), mock_model]
        
        handler = ModelsHandler()
        result = handler.get_model("test-model")
        
        # Should try device_map first, then fallback
        assert mock_auto_model.from_pretrained.call_count == 2
        mock_auto_model.from_pretrained.assert_any_call("test-model", device_map="auto")
        mock_auto_model.from_pretrained.assert_any_call("test-model")
        
        # Should move to CUDA
        mock_model.to.assert_called_once_with("cuda")
        mock_model.eval.assert_called_once()
        assert result == mock_model

    @patch('infrastructure.transformers_engine.models_handler.AutoModelForCausalLM')
    @patch('infrastructure.transformers_engine.models_handler.torch')
    @patch('infrastructure.transformers_engine.models_handler.os')
    def test_should_fallback_to_mps_when_available(self, mock_os, mock_torch, mock_auto_model):
        # Setup mocks
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = True
        mock_os.cpu_count.return_value = 4
        
        mock_model = Mock()
        mock_auto_model.from_pretrained.side_effect = [Exception("Device map failed"), mock_model]
        
        handler = ModelsHandler()
        result = handler.get_model("test-model")
        
        # Should move to MPS
        mock_model.to.assert_called_once_with("mps")
        mock_model.eval.assert_called_once()
        assert result == mock_model

    @patch('infrastructure.transformers_engine.models_handler.AutoModelForCausalLM')
    @patch('infrastructure.transformers_engine.models_handler.torch')
    @patch('infrastructure.transformers_engine.models_handler.os')
    def test_should_fallback_to_xpu_when_available(self, mock_os, mock_torch, mock_auto_model):
        # Setup mocks
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.xpu = Mock()
        mock_torch.xpu.is_available.return_value = True
        mock_os.cpu_count.return_value = 4
        
        mock_model = Mock()
        mock_auto_model.from_pretrained.side_effect = [Exception("Device map failed"), mock_model]
        
        handler = ModelsHandler()
        result = handler.get_model("test-model")
        
        # Should move to XPU
        mock_model.to.assert_called_once_with("xpu")
        mock_model.eval.assert_called_once()
        assert result == mock_model

    @patch('infrastructure.transformers_engine.models_handler.AutoTokenizer')
    @patch('infrastructure.transformers_engine.models_handler.AutoModelForCausalLM')
    @patch('infrastructure.transformers_engine.models_handler.torch')
    @patch('infrastructure.transformers_engine.models_handler.os')
    def test_should_generate_text_with_cuda_device(self, mock_os, mock_torch, mock_auto_model, mock_auto_tokenizer):
        # Setup mocks
        mock_torch.cuda.is_available.return_value = True
        mock_torch.no_grad.return_value.__enter__ = Mock()
        mock_torch.no_grad.return_value.__exit__ = Mock()
        mock_os.cpu_count.return_value = 4
        
        mock_model = Mock()
        mock_auto_model.from_pretrained.return_value = mock_model
        
        mock_tokenizer = Mock()
        mock_tokenizer.pad_token_id = 1234
        mock_auto_tokenizer.from_pretrained.return_value = mock_tokenizer
        
        # Mock tokenizer inputs and outputs
        mock_inputs = {"input_ids": Mock(), "attention_mask": Mock()}
        mock_tokenizer.return_value = mock_inputs
        
        mock_outputs = [Mock()]
        mock_model.generate.return_value = mock_outputs
        
        mock_tokenizer.decode.return_value = "Generated response text"
        
        handler = ModelsHandler()
        result = handler.generate_text("Hello, world!")
        
        # Should tokenize input
        mock_tokenizer.assert_called_with("Hello, world!", return_tensors="pt")
        
        # Should move inputs to CUDA
        for tensor in mock_inputs.values():
            tensor.to.assert_called_with("cuda")
        
        # Should generate with correct parameters
        mock_model.generate.assert_called_once()
        call_kwargs = mock_model.generate.call_args[1]
        assert call_kwargs["max_new_tokens"] == 64
        assert call_kwargs["do_sample"] == False
        assert call_kwargs["top_p"] == 0.9
        assert call_kwargs["temperature"] == 0.7
        assert call_kwargs["pad_token_id"] == 1234
        
        # Should decode output
        mock_tokenizer.decode.assert_called_once_with(mock_outputs[0], skip_special_tokens=True)
        assert result == "Generated response text"

    @patch('infrastructure.transformers_engine.models_handler.AutoTokenizer')
    @patch('infrastructure.transformers_engine.models_handler.AutoModelForCausalLM')
    @patch('infrastructure.transformers_engine.models_handler.torch')
    @patch('infrastructure.transformers_engine.models_handler.os')
    def test_should_use_eos_token_when_no_pad_token(self, mock_os, mock_torch, mock_auto_model, mock_auto_tokenizer):
        # Setup mocks
        mock_torch.cuda.is_available.return_value = False
        mock_torch.no_grad.return_value.__enter__ = Mock()
        mock_torch.no_grad.return_value.__exit__ = Mock()
        mock_os.cpu_count.return_value = 4
        
        mock_model = Mock()
        mock_auto_model.from_pretrained.return_value = mock_model
        
        mock_tokenizer = Mock()
        mock_tokenizer.pad_token_id = None  # No pad token
        mock_tokenizer.eos_token_id = 5678  # Should use this instead
        mock_auto_tokenizer.from_pretrained.return_value = mock_tokenizer
        
        mock_inputs = {"input_ids": Mock(), "attention_mask": Mock()}
        mock_tokenizer.return_value = mock_inputs
        
        mock_outputs = [Mock()]
        mock_model.generate.return_value = mock_outputs
        mock_tokenizer.decode.return_value = "Generated text"
        
        handler = ModelsHandler()
        result = handler.generate_text("Test prompt")
        
        # Should use eos_token_id as pad_token_id
        call_kwargs = mock_model.generate.call_args[1]
        assert call_kwargs["pad_token_id"] == 5678
        assert result == "Generated text"

    @patch('infrastructure.transformers_engine.models_handler.AutoTokenizer')
    @patch('infrastructure.transformers_engine.models_handler.AutoModelForCausalLM')
    @patch('infrastructure.transformers_engine.models_handler.torch')
    @patch('infrastructure.transformers_engine.models_handler.os')
    def test_should_reuse_model_and_tokenizer_on_subsequent_calls(self, mock_os, mock_torch, mock_auto_model, mock_auto_tokenizer):
        # Setup mocks
        mock_torch.cuda.is_available.return_value = False
        mock_torch.no_grad.return_value.__enter__ = Mock()
        mock_torch.no_grad.return_value.__exit__ = Mock()
        mock_os.cpu_count.return_value = 4
        
        mock_model = Mock()
        mock_auto_model.from_pretrained.return_value = mock_model
        
        mock_tokenizer = Mock()
        mock_tokenizer.pad_token_id = 1234
        mock_auto_tokenizer.from_pretrained.return_value = mock_tokenizer
        
        mock_inputs = {"input_ids": Mock(), "attention_mask": Mock()}
        mock_tokenizer.return_value = mock_inputs
        
        mock_outputs = [Mock()]
        mock_model.generate.return_value = mock_outputs
        mock_tokenizer.decode.return_value = "Response"
        
        handler = ModelsHandler()
        
        # First call
        handler.generate_text("First prompt")
        
        # Second call
        handler.generate_text("Second prompt")
        
        # Should only create model and tokenizer once
        mock_auto_model.from_pretrained.assert_called_once()
        mock_auto_tokenizer.from_pretrained.assert_called_once()
        
        # But should tokenize and generate for each call
        assert mock_tokenizer.call_count == 2
        assert mock_model.generate.call_count == 2

    @patch('infrastructure.transformers_engine.models_handler.AutoModelForCausalLM')
    @patch('infrastructure.transformers_engine.models_handler.torch')
    @patch('infrastructure.transformers_engine.models_handler.os')
    def test_should_not_move_to_device_when_no_acceleration_available(self, mock_os, mock_torch, mock_auto_model):
        # Setup mocks - no acceleration available
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = False
        # Mock XPU not available
        mock_torch.xpu = Mock()
        mock_torch.xpu.is_available.return_value = False
        mock_os.cpu_count.return_value = 4
        
        mock_model = Mock()
        mock_auto_model.from_pretrained.side_effect = [Exception("Device map failed"), mock_model]
        
        handler = ModelsHandler()
        result = handler.get_model("test-model")
        
        # Should not call .to() when no acceleration is available
        mock_model.to.assert_not_called()
        mock_model.eval.assert_called_once()
        assert result == mock_model

    @patch('infrastructure.transformers_engine.models_handler.AutoTokenizer')
    @patch('infrastructure.transformers_engine.models_handler.AutoModelForCausalLM')
    @patch('infrastructure.transformers_engine.models_handler.torch')
    @patch('infrastructure.transformers_engine.models_handler.os')
    def test_should_handle_cpu_device_placement_in_generate_text(self, mock_os, mock_torch, mock_auto_model, mock_auto_tokenizer):
        # Setup mocks - only CPU available
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.xpu = Mock()
        mock_torch.xpu.is_available.return_value = False
        mock_torch.no_grad.return_value.__enter__ = Mock()
        mock_torch.no_grad.return_value.__exit__ = Mock()
        mock_os.cpu_count.return_value = 4
        
        mock_model = Mock()
        mock_auto_model.from_pretrained.return_value = mock_model
        
        mock_tokenizer = Mock()
        mock_tokenizer.pad_token_id = 1234
        mock_auto_tokenizer.from_pretrained.return_value = mock_tokenizer
        
        # Mock tokenizer inputs (should NOT be moved to device for CPU)
        mock_inputs = {"input_ids": Mock(), "attention_mask": Mock()}
        mock_tokenizer.return_value = mock_inputs
        
        mock_outputs = [Mock()]
        mock_model.generate.return_value = mock_outputs
        mock_tokenizer.decode.return_value = "CPU generated text"
        
        handler = ModelsHandler()
        result = handler.generate_text("CPU test")
        
        # Should NOT move inputs to any device (stays on CPU)
        for tensor in mock_inputs.values():
            tensor.to.assert_not_called()
        
        assert result == "CPU generated text"
