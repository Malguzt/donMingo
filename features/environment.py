import os
import importlib
import features.steps.responde_zulip_steps
from features.steps.mocks.zulip_api_mock import zulip_mock_server
from features.steps.responde_zulip_steps import given_system_is_configured as system_configured_step_impl


def before_all(context):
    zulip_mock_server.start(port=8000)
    context.zulip_api_url = "http://127.0.0.1:8000"

def after_all(context):
    zulip_mock_server.stop()

def before_scenario(context, scenario):
    # Force reload the mock module to ensure latest changes are picked up
    importlib.reload(features.steps.responde_zulip_steps)

    zulip_mock_server.reset()
    os.environ["ZULIP_API_URL"] = context.zulip_api_url
    os.environ["ZULIP_API_KEY"] = "test_api_key"
    os.environ["ZULIP_EMAIL"] = "test@example.com"
    # Call the system configured step to ensure context.guanacos_spits is initialized
    system_configured_step_impl(context)
