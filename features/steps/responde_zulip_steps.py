from behave import given, when, then
import os
import threading
import time
from src.infrastructure.repositories.zulip_chat_message_repository import ZulipChatMessageRepository
from features.steps.fake_think_repository import FakeThinkRepository
from src.infrastructure.repositories.local_guanacos_repository import LocalGuanacosRepository
from src.application.use_cases.guanacos_spits import GuanacosSpits
from src.domain.entities.guanaco.guanaco import Guanaco
from src.domain.entities.user import User
from features.steps.mocks.zulip_api_mock import zulip_mock_server

@given('the Zulip API credentials are set as environment variables:') # type: ignore
def given_zulip_api_credentials_env_vars(context):
    for row in context.table:
        os.environ["ZULIP_API_KEY"] = row["ZULIP_API_KEY"].strip('"')
        os.environ["ZULIP_EMAIL"] = row["ZULIP_EMAIL"].strip('"')
        os.environ["ZULIP_API_URL"] = row.get("ZULIP_SITE", row.get("ZULIP_API_URL", "")).strip('"')

@given('a mocked Zulip server is running') # type: ignore
def given_mocked_zulip_server_running(context):
    # The mock server is started in before_all hook
    pass

@given('the Zulip API have the following credentials') # type: ignore
def given_zulip_api_have_credentials(context):
    # Credentials are set in before_scenario as environment variables
    for row in context.table:
        api_key = row["api_key"]
        zulip_mock_server.config["api_key"] = api_key
        os.environ["ZULIP_API_KEY"] = api_key

@given('the Zulip API Mock have a GET /api/v1/messages endpoint to get the messages mocking what this document describe: https://zulip.com/api/get-messages') # type: ignore
def given_zulip_api_mock_get_messages(context):
    # This is handled by the zulip_api_mock_server.py
    pass

@given('the Zulip API Mock have a POST /api/v1/messages endpoint to send messages mocking what this document describe: https://zulip.com/api/send-message') # type: ignore
def given_zulip_api_mock_post_messages(context):
    # This is handled by the zulip_api_mock_server.py
    pass

@given('the Zulip API Mock have a POST /api/v1/mark_topic_as_read endpoint to mark messages as read mocking what this document describe: https://zulip.com/api/mark-topic-as-read') # type: ignore
def given_zulip_api_mock_post_mark_topic_as_read(context):
    # This is handled by the zulip_api_mock_server.py
    pass

@given('the Zulip API is accessible') # type: ignore
def given_zulip_api_accessible(context):
    # The mock server is running and accessible via the URL set in before_all
    pass

@given('the mocked responses a list of 3 unread topic') # type: ignore
def given_mocked_responses_unread_topics(context):
    unread_topics = []
    for row in context.table:
        unread_topics.append({
            "topic_id": int(row["topic_id"]),
            "topic_name": row["topic_name"].strip('"\''),
            "unread_count": int(row["unread_count"]),
            "content": row["content"].strip('"\'')
        })
    zulip_mock_server.add_unread_topics_response(unread_topics)

@given('the system is configured') # type: ignore
def given_system_is_configured(context):
    context.chat_message_repository = ZulipChatMessageRepository()
    context.think_repository = FakeThinkRepository()
    guanacos_repository = LocalGuanacosRepository()
    guanacos_repository.get_guanacos = lambda: [
        Guanaco(
            name="test_guanaco",
            user=User(platform_id="user@example.com", platform="zulip"),
            chat_message_repository=context.chat_message_repository,
            think_repository=context.think_repository,
        )
    ]
    print(f"[DEBUG] guanacos_repository.get_guanacos() returns: {guanacos_repository.get_guanacos()}")
    context.guanacos_spits = GuanacosSpits(guanacos_repository, sleep_time=1)

@when('the system processes each unread topic') # type: ignore
def when_processes_each_unread_topic(context):
    context.main_thread = threading.Thread(target=context.guanacos_spits.run)
    context.main_thread.start()
    time.sleep(5)
    context.guanacos_spits.stop()
    context.main_thread.join()

@then('it should send a response to each topic using the official Zulip Client Class') # type: ignore
def then_should_send_response_to_each_topic_using_official_client_class(context):
    sent_messages = zulip_mock_server.get_sent_messages()
    assert len(sent_messages) == len(context.table.rows), f"Expected {len(context.table.rows)} messages, but got {len(sent_messages)}"
    for row in context.table:
        topic_id = int(row["topic_id"])
        response_message = row["response_message"].strip('"\'')
        found = False
        for message in sent_messages:
            if message["to"] == topic_id and message["content"] == response_message:
                found = True
                break
        assert found, f"Response for topic '{topic_id}' not sent or content mismatch"

@then('it should mark each topic as read after responding using the official Zulip Client Class') # type: ignore
def then_should_mark_each_topic_as_read_after_responding_using_official_client_class(context):
    read_topics = zulip_mock_server.get_read_topics()
    expected_topic_ids = [int(row["topic_id"]) for row in context.table]
    assert len(read_topics) == len(expected_topic_ids), f"Expected {len(expected_topic_ids)} topics to be marked as read, but got {len(read_topics)}"
    for topic_id in expected_topic_ids:
        assert topic_id in read_topics, f"Topic {topic_id} was not marked as read"

@given(u'the mocked responses a list of 2 unread topic on the first call')
def step_impl(context):
    unread_topics = []
    for row in context.table:
        unread_topics.append({
            "topic_id": int(row["topic_id"]),
            "topic_name": row["topic_name"].strip('"\''),
            "unread_count": int(row["unread_count"]),
            "content": row["content"].strip('"\'')
        })
    zulip_mock_server.add_unread_topics_response(unread_topics)

@given(u'the mocked responses an empty list of unread topic on the second call')
def step_impl(context):
    zulip_mock_server.add_unread_topics_response([])

@when(u'the system runs for 2 iterations of checking for unread topics and responding')
def step_impl(context):
    context.main_thread = threading.Thread(target=context.guanacos_spits.run)
    context.main_thread.start()
    time.sleep(10) # Run for longer to allow for multiple iterations
    context.guanacos_spits.stop()
    context.main_thread.join()

@then(u'it should send a response to each topic in the first iteration using the official Zulip Client Class')
def step_impl(context):
    sent_messages = zulip_mock_server.get_sent_messages()
    assert len(sent_messages) == len(context.table.rows), f"Expected {len(context.table.rows)} messages, but got {len(sent_messages)}"
    for row in context.table:
        topic_id = int(row["topic_id"])
        response_message = row["response_message"].strip('"\'')
        found = False
        for message in sent_messages:
            if message["to"] == topic_id and message["content"] == response_message:
                found = True
                break
        assert found, f"Response for topic '{topic_id}' not sent or content mismatch"

@then(u'it should mark each topic as read after responding in the first iteration using the official Zulip Client Class')
def step_impl(context):
    read_topics = zulip_mock_server.get_read_topics()
    expected_topic_ids = [int(row["topic_id"]) for row in context.table]
    assert len(read_topics) == len(expected_topic_ids), f"Expected {len(expected_topic_ids)} topics to be marked as read, but got {len(read_topics)}"
    for topic_id in expected_topic_ids:
        assert topic_id in read_topics, f"Topic {topic_id} was not marked as read"

@then(u'it should not send any response in the second iteration since there are no unread topics')
def step_impl(context):
    # The number of sent messages should be the same as in the first iteration
    sent_messages = zulip_mock_server.get_sent_messages()
    assert len(sent_messages) == 2, f"Expected 2 messages from the first iteration, but got {len(sent_messages)}"

@then(u'it should not mark any topics as read in the second iteration since there are no unread topics')
def step_impl(context):
    # The number of read topics should be the same as in the first iteration
    read_topics = zulip_mock_server.get_read_topics()
    assert len(read_topics) == 2, f"Expected 2 topics marked as read from the first iteration, but got {len(read_topics)}"

@given(u'the think repository is configured with the following responses:')
def step_impl(context):
    context.think_repository.reset()
    for row in context.table:
        context.think_repository.add_response(row["text"].strip('"\''), row["response"].strip('"\''))