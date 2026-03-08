from domain.ports.chat_message_repository import ChatMessageRepository
from domain.entities.user import User
from domain.errors import MissingUserError, MissingRepositoryError
from domain.ports.think_repository import ThinkRepository
from prometheus_client import Counter, Summary
import time

# Define Prometheus metrics
MSGS_PROCESSED = Counter('messages_processed_total', 'Total messages processed', ['guanaco_name'])
THINK_DURATION = Summary('think_duration_seconds', 'Time spent processing messages', ['guanaco_name'])

class Guanaco:
    def __init__(self, name: str = None, user: User = None, chat_message_repository: ChatMessageRepository = None, think_repository: ThinkRepository = None):
        self.name = name
        self.user = user
        self.chat_message_repository = chat_message_repository
        self.think_repository = think_repository

    def work(self):
        """Process unread messages once. Returns True if work was performed, False otherwise."""
        if self.user is None:
            raise MissingUserError("Cannot work without a user")
        
        if self.chat_message_repository is None:
            raise MissingRepositoryError("Cannot work without a chat message repository")
        
        if self.think_repository is None:
            raise MissingRepositoryError("Cannot work without a think repository")
        
        channels = self.chat_message_repository.get_streams_with_unread_messages()
        work_performed = False
        
        for channel in channels.values():
            print(f"Channel: {channel}")
            last_message = channel.get_last_message()
            if last_message.sender != self.user:
                start_time = time.time()
                
                # Processing message
                response_text = self.think_repository.get_think(last_message.content)
                channel.respond(response_text)
                
                # Record metrics
                THINK_DURATION.labels(guanaco_name=self.name).observe(time.time() - start_time)
                MSGS_PROCESSED.labels(guanaco_name=self.name).inc()
                
                work_performed = True
        
        if work_performed:
            print(f"{self.name} has processed messages")
        
        return work_performed