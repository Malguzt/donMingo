Feature: Responde Zulip Integration

    The Guanaco project integrates with Zulip to enhance communication and collaboration. 
    For this, the system works in a loop getting unread messages, processing them, and sending responses.
    Test must run with the timout of 30 seconds, because the system run in a infinite loop.

    Scenario: Response unread topics from Zulip
        Given the Zulip API is accessible
        And the mocked Zulip server is running
        And the mocked responses a list of 3 unread topic
          | topic_id | topic_name       | unread_count |
          | 1        | "Test Topic"     | 5            |
          | 2        | "Another Topic"  | 3            |
          | 3        | "Third Topic"    | 8            |
        When the system processes each unread topic
        Then it should send a response to each topic
          | topic_id | response_message               |
          | 1        | "Response to Test Topic"       |
          | 2        | "Response to Another Topic"    |
          | 3        | "Response to Third Topic"      |
        When the system marks topics as read
        Then it should confirm that all topics are marked as read