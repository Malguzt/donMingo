from abc import ABC, abstractmethod
from typing import List
from domain.entities.guanaco.guanaco import Guanaco

class GuanacosRepository(ABC):

    @abstractmethod
    def get_guanacos(self) -> List[Guanaco]:
        raise NotImplementedError("Not implemented")