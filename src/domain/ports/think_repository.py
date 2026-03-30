from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

class ModelComplexity(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"

class ModelSpecialty(Enum):
    GENERAL = "general"
    CODING = "coding"
    REASONING = "reasoning"

class ThinkRepository(ABC):
    @abstractmethod
    def get_think(self, message: str, required_complexity: Optional[ModelComplexity] = None) -> str:
        raise NotImplementedError("Not implemented")