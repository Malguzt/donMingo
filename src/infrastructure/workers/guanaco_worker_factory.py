from application.ports.worker_factory import WorkerFactory, WorkerHandle
from domain.entities.guanaco.guanaco import Guanaco
from infrastructure.workers.guanaco_worker import GuanacoWorker


class GuanacoWorkerFactory(WorkerFactory):
    """Infrastructure implementation that builds thread-based Guanaco workers."""

    def create(self, guanaco: Guanaco, sleep_time: int) -> WorkerHandle:
        return GuanacoWorker(guanaco, sleep_time)
