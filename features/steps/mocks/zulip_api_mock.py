from fastapi import FastAPI, Request, Response, status
from pydantic import BaseModel
import uvicorn
import threading
import time
import json

class Message(BaseModel):
    type: str
    to: int
    content: str
    topic: str

class Server(uvicorn.Server):
    def handle_exit(self, sig: int, frame) -> None:
        self.should_exit = True

class ZulipAPIMock:
    def __init__(self):
        self.app = FastAPI()
        self.unread_topics = []
        self.sent_messages = []
        self.read_topics = []
        self.server_thread = None
        self.config = {"api_key": "default_api_key"}
        self._server = None # To hold the uvicorn server instance

        @self.app.get("/api/v1/messages")
        async def get_messages(request: Request):
            messages = []
            for topic in self.unread_topics:
                messages.append({
                    "id": topic["topic_id"],
                    "type": "stream",
                    "stream_id": topic["topic_id"],
                    "topic_id": topic["topic_id"],
                    "subject": topic["topic_name"],
                    "content": topic.get("content", f"Content for {topic['topic_name']}"),
                    "sender_id": "test@example.com",
                    "sender_email": "test@example.com",
                    "timestamp": time.time(),
                    "unread": True,
                    "flags": ["unread"]
                })
            return {"messages": messages, "result": "success"}

        @self.app.post("/api/v1/messages")
        async def send_message(message: Message):
            self.sent_messages.append(message.dict())
            return {"result": "success", "id": len(self.sent_messages)}

        @self.app.post("/api/v1/mark_topic_as_read")
        async def mark_topic_as_read(request: Request):
            data = await request.json()
            topic_id = data.get("topic_id")
            if topic_id:
                self.read_topics.append(topic_id)
                return {"result": "success"}
            return Response(status_code=status.HTTP_400_BAD_REQUEST)

        @self.app.get("/api/v1/users/me")
        async def get_users_me():
            return {
                "result": "success",
                "msg": "",
                "user_id": 1,
                "email": "test@example.com",
                "full_name": "Test User",
            }

        @self.app.get("/api/v1/server_settings")
        async def get_server_settings():
            return {
                "result": "success",
                "msg": "",
                "realm_name": "Zulip Test",
                "realm_uri": "http://127.0.0.1:8000",
                "zulip_version": "5.0-dev",
                "push_notifications_enabled": False,
                "email_auth_enabled": True,
                "authentication_methods": {
                    "dev": False,
                    "email": True,
                    "github": False,
                    "ldap": False,
                    "password": True,
                    "remoteuser": False
                },
            }

    def set_unread_topics(self, topics):
        self.unread_topics = topics

    def get_sent_messages(self):
        return self.sent_messages

    def get_read_topics(self):
        return self.read_topics

    def start(self, port=8000):
        config = uvicorn.Config(self.app, host="127.0.0.1", port=port, log_level="info")
        self._server = Server(config=config)
        self.server_thread = threading.Thread(target=self._server.run)
        self.server_thread.daemon = True
        self.server_thread.start()
        time.sleep(3) # Give the server a moment to start

    def stop(self):
        if self._server:
            self._server.should_exit = True
            self.server_thread.join() # Wait for the server thread to finish

    def reset(self):
        self.unread_topics = []
        self.sent_messages = []
        self.read_topics = []
        self.config = {"api_key": "default_api_key"}

zulip_mock_server = ZulipAPIMock()

if __name__ == "__main__":
    zulip_mock_server.start()
    print("Zulip Mock Server running on http://127.0.0.1:8000")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        zulip_mock_server.stop()
        print("Zulip Mock Server stopped.")