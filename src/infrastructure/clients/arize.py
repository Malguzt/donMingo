from infrastructure.config.arize_config import ArizeConfig
import arize

class ArizeClient:
    def __init__(self):
        self.arize_config = ArizeConfig()
        self.arize_client = arize.Client(
            api_key=self.arize_config.api_key,
            api_url=self.arize_config.api_url
        )

    def get_prompt(self, prompt: str) -> str:
        return self.arize_client.get_prompt(prompt)