from domain.ports.think_repository import ThinkRepository
from infrastructure.transformers_engine.models_handler import ModelsHandler
from infrastructure.transformers_engine.model_catalog import ModelComplexity

class TransformersThinkRepository(ThinkRepository):
    def __init__(self):
        self.transformers_engine = ModelsHandler()

    def get_think(self, message: str, required_complexity: ModelComplexity = None) -> str:
        if required_complexity is None:
            return self.transformers_engine.generate_text(message)
        return self.transformers_engine.generate_text(message, required_complexity=required_complexity)
