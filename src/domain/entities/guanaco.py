from domain.ports.chat_message_repository import ChatMessageRepository
from domain.entities.user import User
from time import sleep

class Guanaco:
    def __init__(self, name: str, user: User, chat_message_repository: ChatMessageRepository):
        self.name = name
        self.user = user
        self.chat_message_repository = chat_message_repository

    def work(self):
        channels = self.chat_message_repository.get_streams_with_unread_messages()
        for channel in channels.values():
            print(f"Channel: {channel}")
            if channel.get_last_message().sender != self.user:
                channel.respond("Respondiendo canales ahora")
        print(f"{self.name} has worked, going to sleep for 10 seconds...")
        sleep(10)
        self.work()