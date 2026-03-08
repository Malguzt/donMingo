import pytest
from unittest.mock import MagicMock
from infrastructure.repositories.zulip_bot_manager import ZulipBotManager

@pytest.fixture
def mock_zulip_config(monkeypatch):
    monkeypatch.setenv("ZULIP_API_KEY", "fake_key")
    monkeypatch.setenv("ZULIP_EMAIL", "fake@example.com")
    monkeypatch.setenv("ZULIP_SITE", "https://fake.zulipchat.com")

@pytest.fixture
def zulip_bot_manager(mock_zulip_config):
    manager = ZulipBotManager()
    manager.client = MagicMock()
    return manager

def test_create_bot_success(zulip_bot_manager):
    # Mocking the Zulip client call_endpoint method
    zulip_bot_manager.client.call_endpoint.return_value = {
        "result": "success",
        "api_key": "some_new_api_key"
    }
    
    api_key = zulip_bot_manager.create_bot("Test Bot", "test_bot")
    
    assert api_key == "some_new_api_key"
    zulip_bot_manager.client.call_endpoint.assert_called_once_with(
        url="bots",
        method="POST",
        request={
            "full_name": "Test Bot",
            "short_name": "test_bot",
            "bot_type": 1,
        }
    )

def test_create_bot_failure(zulip_bot_manager):
    zulip_bot_manager.client.call_endpoint.return_value = {
        "result": "error",
        "msg": "Invalid name"
    }
    
    with pytest.raises(RuntimeError, match="Error creating bot Test Bot: Invalid name"):
        zulip_bot_manager.create_bot("Test Bot", "test_bot")

def test_deactivate_bot_success(zulip_bot_manager):
    # Mock finding the user ID
    zulip_bot_manager.client.get_users.return_value = {
        "result": "success",
        "members": [{"email": "test_bot@example.com", "user_id": 123}]
    }
    
    # Mock deactivation response
    zulip_bot_manager.client.call_endpoint.return_value = {
        "result": "success"
    }

    result = zulip_bot_manager.deactivate_bot("test_bot@example.com")
    
    assert result is True
    zulip_bot_manager.client.call_endpoint.assert_called_once_with(
        url="users/123",
        method="DELETE"
    )

def test_deactivate_bot_not_found(zulip_bot_manager):
    # Mock finding the user ID (not found = empty members list)
    zulip_bot_manager.client.get_users.return_value = {
        "result": "success",
        "members": []
    }
    
    with pytest.raises(ValueError, match="Bot with email test_bot@example.com not found"):
        zulip_bot_manager.deactivate_bot("test_bot@example.com")
        
def test_deactivate_bot_failure(zulip_bot_manager):
    # Mock finding the user ID
    zulip_bot_manager.client.get_users.return_value = {
        "result": "success",
        "members": [{"email": "test_bot@example.com", "user_id": 123}]
    }
    
    # Mock deactivation error
    zulip_bot_manager.client.call_endpoint.return_value = {
        "result": "error",
        "msg": "Missing permissions"
    }

    with pytest.raises(RuntimeError, match="Error deactivating bot test_bot@example.com: Missing permissions"):
        zulip_bot_manager.deactivate_bot("test_bot@example.com")

def test_bot_exists_true(zulip_bot_manager):
    zulip_bot_manager.client.get_users.return_value = {
        "result": "success",
        "members": [{"full_name": "Recursos Humanos", "email": "rh@example.com"}]
    }
    
    # Should be case-insensitive
    assert zulip_bot_manager.bot_exists("recursos humanos") is True

def test_bot_exists_false(zulip_bot_manager):
    zulip_bot_manager.client.get_users.return_value = {
        "result": "success",
        "members": [{"full_name": "Otro Bot", "email": "otro@example.com"}]
    }
    
    assert zulip_bot_manager.bot_exists("Recursos Humanos") is False

def test_bot_exists_api_error(zulip_bot_manager):
    zulip_bot_manager.client.get_users.return_value = {
        "result": "error",
        "msg": "Invalid API key"
    }
    
    with pytest.raises(RuntimeError, match="Zulip API error retrieving users: Invalid API key"):
        zulip_bot_manager.bot_exists("Recursos Humanos")

