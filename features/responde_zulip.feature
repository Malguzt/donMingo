Feature: Responde Zulip Integration

    The Guanaco project integrates with Zulip to enhance communication and collaboration. 
    For this, the system works in a loop getting unread messages, processing them, and sending responses.
    Test must run with the timout of 30 seconds, because the system run in a infinite loop.

    Background: Dependencies mockes
        Given a mocked Zulip server is running
        And the Zulip API credentials are set as environment variables:
          | ZULIP_API_KEY  | ZULIP_EMAIL | ZULIP_SITE |
          | "test_api_key"  | "test@example.com" | "https://127.0.0.1:59485" |
        And the Zulip API Mock have a GET /api/v1/messages endpoint to get the messages mocking what this document describe: https://zulip.com/api/get-messages
        And the Zulip API Mock have a POST /api/v1/messages endpoint to send messages mocking what this document describe: https://zulip.com/api/send-message
        And the Zulip API Mock have a POST /api/v1/mark_topic_as_read endpoint to mark messages as read mocking what this document describe: https://zulip.com/api/mark-topic-as-read
    
    Scenario: Response unread topics from Zulip
        Given the mocked responses a list of 3 unread topic
          | topic_id | topic_name       | unread_count |
          | 1        | "Test Topic"     | 5            |
          | 2        | "Another Topic"  | 3            |
          | 3        | "Third Topic"    | 8            |
        When the system processes each unread topic
        Then it should send a response to each topic using the official Zulip Client Class
          | topic_id | response_message               |
          | 1        | "Response to Test Topic"       |
          | 2        | "Response to Another Topic"    |
          | 3        | "Response to Third Topic"      |
        And it should mark each topic as read after responding using the official Zulip Client Class
          | topic_id |
          | 1        |
          | 2        |
          | 3        |