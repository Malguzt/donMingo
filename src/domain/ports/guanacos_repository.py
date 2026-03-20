from abc import ABC, abstractmethod
from typing import List
from domain.entities.guanaco.guanaco import Guanaco

class GuanacosRepository(ABC):

    @abstractmethod
    def get_guanacos(self) -> List[Guanaco]:
        raise NotImplementedError("Not implemented")

    @abstractmethod
    def save_guanaco(self, name: str, short_name: str, email: str, api_key: str, bot_type: str = "guanaco"):
        raise NotImplementedError("Not implemented")

    @abstractmethod
    def delete_guanaco(self, short_name: str):
        raise NotImplementedError("Not implemented")