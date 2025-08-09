from domain.ports.chat_message_repository import ChatMessageRepository
from domain.entities.user import User
from time import sleep

class Guanaco:
    def __init__(self, name: str, user: User, chat_message_repository: ChatMessageRepository):
        self.name = name
        self.user = user
        self.chat_message_repository = chat_message_repository

    def work(self):
        messages = self.chat_message_repository.get_unread_messages(self.user)
        for message in messages:
            print(f"Message: {message.content}")
            print(f"Sender: {message.sender.name}")
            print(f"Receiver: {message.receiver.name}")
            print(f"Created at: {message.created_at}")
            if message.sender.email == self.user.email:
                self.chat_message_repository.send_private_message(f"Hola {message.sender.name}", message.sender)
                self.chat_message_repository.mark_as_read(message)
        print(f"{self.name} has worked, total messages: {len(messages)}, going to sleep for 10 seconds...")
        sleep(10)
        self.work()