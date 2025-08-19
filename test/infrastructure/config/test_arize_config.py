import pytest
import os
from unittest.mock import patch
from infrastructure.config.arize_config import ArizeConfig


class TestArizeConfig:
    @patch.dict(os.environ, {"ARIZE_API_KEY": "test_key", "ARIZE_API_URL": "test_url"})
    def test_should_load_config_from_environment_variables(self):
        config = ArizeConfig()
        
        assert config.api_key == "test_key"
        assert config.api_url == "test_url"

    @patch.dict(os.environ, {}, clear=True)
    def test_should_handle_missing_environment_variables(self):
        config = ArizeConfig()
        
        assert config.api_key is None
        assert config.api_url is None
