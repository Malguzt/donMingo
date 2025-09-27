from domain.ports.think_repository import ThinkRepository
from infrastructure.transformers_engine.models_handler import ModelsHandler


class TransformersThinkRepository(ThinkRepository):
    def __init__(self):
        self.transformers_engine = ModelsHandler()

    def get_think(self, message: str) -> str:
        return self.transformers_engine.generate_text(message)
