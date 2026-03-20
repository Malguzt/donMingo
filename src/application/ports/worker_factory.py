from abc import ABC, abstractmethod
from typing import Protocol
from domain.entities.guanaco.guanaco import Guanaco


class WorkerHandle(Protocol):
    def start(self) -> None:
        ...

    def stop(self) -> None:
        ...

    def is_running(self) -> bool:
        ...


class WorkerFactory(ABC):
    @abstractmethod
    def create(self, guanaco: Guanaco, sleep_time: int) -> WorkerHandle:
        raise NotImplementedError("Not implemented")
