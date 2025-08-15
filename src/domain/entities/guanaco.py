from domain.ports.chat_message_repository import ChatMessageRepository
from domain.entities.user import User
from time import sleep
from domain.ports.think_repository import ThinkRepository

class Guanaco:
    def __init__(self, name: str, user: User, chat_message_repository: ChatMessageRepository, think_repository: ThinkRepository):
        self.name = name
        self.user = user
        self.chat_message_repository = chat_message_repository
        self.think_repository = think_repository

    def work(self):
        channels = self.chat_message_repository.get_streams_with_unread_messages()
        for channel in channels.values():
            print(f"Channel: {channel}")
            if channel.get_last_message().sender != self.user:
                channel.respond(self.think_repository.get_think(channel.get_last_message().content))
        print(f"{self.name} has worked, going to sleep for 10 seconds...")
        sleep(10)
        self.work()