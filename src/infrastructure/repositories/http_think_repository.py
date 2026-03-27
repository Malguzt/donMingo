import requests
from domain.ports.think_repository import ThinkRepository, ModelComplexity
import os

class HttpThinkRepository(ThinkRepository):
    """
    Implementation of ThinkRepository that calls the Yaguarete LLM Proxy via HTTP.
    """
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("YAGUARETE_URL", "http://localhost:8001")
        self.model_id = os.getenv("YAGUARETE_MODEL", "Qwen/Qwen2.5-7B-Instruct")

    def get_think(self, message: str, required_complexity: ModelComplexity = None) -> str:
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": message}]
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[ERROR] Failed to get response from Yaguarete: {e}")
            return "Lo siento, tuve un problema al procesar tu solicitud con el servicio de modelos."
