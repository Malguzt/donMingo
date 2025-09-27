from src.domain.ports.think_repository import ThinkRepository

class FakeThinkRepository(ThinkRepository):
    def get_think(self, text: str) -> str:
        if text == "Hello":
            return "Response to Test Topic"
        elif text == "Hello again":
            return "Response to Another Topic"
        elif text == "Hi there":
            return "Response to Third Topic"
        return ""
