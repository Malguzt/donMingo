from domain.entities.guanaco import Guanaco
from domain.entities.user import User
from infrastructure.repositories.zulip_chat_message_repository import ZulipChatMessageRepository
from concurrent.futures import ThreadPoolExecutor

class GuanacosSpits:
    def __init__(self):
        self.guanacos = [
            Guanaco(
                name="Pancho", 
                user=User(
                    id=1, 
                    name="Paco", 
                    email="paco-bot@donmingo.zulipchat.com"), 
                chat_message_repository=ZulipChatMessageRepository()),
        ]

    def run(self):
        with ThreadPoolExecutor(max_workers=len(self.guanacos)) as executor:
            futures = [executor.submit(guanaco.work) for guanaco in self.guanacos]
            for future in futures:
                future.result()