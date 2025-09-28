from src.domain.ports.think_repository import ThinkRepository

class FakeThinkRepository(ThinkRepository):
    def __init__(self):
        self.responses = {
            "Hello": "Response to Test Topic",
            "Hello again": "Response to Another Topic",
            "Hi there": "Response to Third Topic"
        }

    def get_think(self, text: str) -> str:
        return self.responses.get(text, "")

    def add_response(self, text: str, response: str):
        self.responses[text] = response

    def reset(self):
        self.responses = {}
