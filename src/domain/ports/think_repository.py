from abc import ABC, abstractmethod

class ThinkRepository(ABC):
    @abstractmethod
    def get_think(self, message: str) -> str:
        raise NotImplementedError("Not implemented")