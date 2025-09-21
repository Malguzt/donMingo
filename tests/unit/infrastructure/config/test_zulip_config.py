import pytest
import os
from unittest.mock import patch
from infrastructure.config.zulip_config import ZulipConfig


class TestZulipConfig:
    THRE_VAIALBLES_MISSING = "Missing required environment variables: ZULIP_API_KEY, ZULIP_EMAIL, ZULIP_SITE"
    EMAIL_SITE_MISSING = "Missing required environment variables: ZULIP_EMAIL, ZULIP_SITE"
    APIKEY_SITE_MISSING = "Missing required environment variables: ZULIP_SITE"
    APIKEY_APIKEY_MISSING = "Missing required environment variables: ZULIP_API_KEY"

    @patch.dict(os.environ, {
        "ZULIP_API_KEY": "test_key",
        "ZULIP_EMAIL": "test@example.com",
        "ZULIP_SITE": "test.zulipchat.com"
    })
    def test_should_load_config_from_environment_variables(self):
        config = ZulipConfig()
        
        assert config.api_key == "test_key"
        assert config.email == "test@example.com"
        assert config.site == "test.zulipchat.com"

    @patch.dict(os.environ, {}, clear=True)
    def test_should_raise_error_when_all_environment_variables_missing(self):
        with pytest.raises(ValueError, match=TestZulipConfig.THRE_VAIALBLES_MISSING):
            ZulipConfig()

    @patch.dict(os.environ, {"ZULIP_API_KEY": "test_key"}, clear=True)
    def test_should_raise_error_when_some_environment_variables_missing(self):
        with pytest.raises(ValueError, match=TestZulipConfig.EMAIL_SITE_MISSING):
            ZulipConfig()

    @patch.dict(os.environ, {"ZULIP_API_KEY": "test_key", "ZULIP_EMAIL": "test@example.com"}, clear=True)
    def test_should_raise_error_when_only_site_missing(self):
        with pytest.raises(ValueError, match=TestZulipConfig.APIKEY_SITE_MISSING):
            ZulipConfig()

    @patch.dict(
        os.environ,
        {"ZULIP_API_KEY": "", "ZULIP_EMAIL": "test@example.com", "ZULIP_SITE": "test.zulipchat.com"},
        clear=True)
    def test_should_raise_error_when_environment_variable_is_empty_string(self):
        with pytest.raises(ValueError, match=TestZulipConfig.APIKEY_APIKEY_MISSING):
            ZulipConfig()
