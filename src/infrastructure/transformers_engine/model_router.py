from typing import Optional
from .model_catalog import ModelCatalog, ModelComplexity, ModelSpecialty, ModelDefinition

class ModelRouter:
    """Decides which model to use based on the prompt characteristics and requirements."""

    def __init__(self, catalog: ModelCatalog):
        self.catalog = catalog

    def route_prompt(self, prompt: str, required_complexity: Optional[ModelComplexity] = None) -> ModelDefinition:
        """
        Analyzes the prompt and returns the best model definition to use.
        """
        # Determine Specialty
        specialty = self._determine_specialty(prompt)
        
        # Determine Complexity (if not explicitly requested)
        if required_complexity is None:
            required_complexity = self._determine_complexity(prompt, specialty)

        # Find model in catalog
        model_def = self.catalog.find_best_model(required_complexity, specialty)
        
        if model_def is None:
            # Fallback
            model_def = self.catalog.get_default_model()
            
        return model_def

    def _determine_specialty(self, prompt: str) -> ModelSpecialty:
        """Simple heuristic to determine if it's a coding or general question."""
        code_keywords = ["python", "code", "código", "function", "función", "bash", "html", "css", "javascript", "bug", "error", "refactor"]
        lower_prompt = prompt.lower()
        
        if any(keyword in lower_prompt for keyword in code_keywords):
            return ModelSpecialty.CODE
            
        reasoning_keywords = ["analyze", "analiza", "evaluate", "evalúa", "compare", "compara", "plan", "architecture", "arquitectura", "solve", "resuelve", "why", "por qué"]
        if any(keyword in lower_prompt for keyword in reasoning_keywords):
            return ModelSpecialty.REASONING
            
        return ModelSpecialty.CHAT

    def _determine_complexity(self, prompt: str, specialty: ModelSpecialty) -> ModelComplexity:
        """
        Determine how complex the model needs to be.
        Complex reasoning or very long prompts need larger models.
        """
        if specialty == ModelSpecialty.REASONING:
            return ModelComplexity.LARGE
            
        # If the prompt is very long, it might need a larger context model,
        # but for now we correlate prompt length with task complexity.
        if len(prompt) > 1000:
            return ModelComplexity.MEDIUM
            
        return ModelComplexity.SMALL
