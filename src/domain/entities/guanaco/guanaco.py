from domain.entities.user import User
from domain.errors import MissingRepositoryError, MissingUserError
from domain.ports.chat_message_repository import ChatMessageRepository
from domain.ports.think_repository import ThinkRepository


class Guanaco:
    def __init__(
        self,
        name: str | None = None,
        user: User | None = None,
        chat_message_repository: ChatMessageRepository | None = None,
        think_repository: ThinkRepository | None = None,
    ):
        self.name = name
        self.user = user
        self.chat_message_repository = chat_message_repository
        self.think_repository = think_repository

    def work(self):
        print("[DEBUG] Guanaco.work() called")
        """Process unread messages once. Returns True if work was performed, False otherwise."""
        if self.user is None:
            raise MissingUserError("Cannot work without a user")

        if self.chat_message_repository is None:
            raise MissingRepositoryError(
                "Cannot work without a chat message repository"
            )

        if self.think_repository is None:
            raise MissingRepositoryError("Cannot work without a think repository")

        channels = self.chat_message_repository.get_streams_with_unread_messages()
        work_performed = False

        for channel in channels.values():
            print(f"Channel: {channel}")
            print(f"[DEBUG] channel.get_last_message().sender: {channel.get_last_message().sender}")
            print(f"[DEBUG] self.user: {self.user}")
            if channel.get_last_message().sender != self.user:
                channel.respond(
                    self.think_repository.get_think(channel.get_last_message().content)
                )
                work_performed = True

        if work_performed:
            print(f"{self.name} has processed messages")

        return work_performed
