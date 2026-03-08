from domain.entities.guanaco.guanaco import Guanaco
from domain.entities.user import User
from domain.ports.guanacos_repository import GuanacosRepository
from infrastructure.repositories.zulip_chat_message_repository import ZulipChatMessageRepository
from infrastructure.repositories.transformers_think_repository import TransformersThinkRepository
from infrastructure.repositories.hr_think_repository import HRThinkRepository

class LocalGuanacosRepository(GuanacosRepository):
    def get_guanacos(self):
        return [
            Guanaco(
                name="Pancho", 
                user=User(
                    platform_id=1, 
                    platform="zulip",
                    name="Paco"), 
                chat_message_repository=ZulipChatMessageRepository(),
                think_repository=TransformersThinkRepository()),
            Guanaco(
                name="Recursos Humanos", 
                user=User(
                    platform_id=1, # This bot is not filtering messages yet, any user will trigger HR Bot to respond since its configured from Zulip to listen 
                    platform="zulip",
                    name="Recursos Humanos"), 
                chat_message_repository=ZulipChatMessageRepository(),
                think_repository=HRThinkRepository()),
        ]