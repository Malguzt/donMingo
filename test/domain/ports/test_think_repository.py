import pytest
from domain.ports.think_repository import ThinkRepository

class TestThinkRepository:
    def test_should_rais_not_implemented_error_when_calling_get_think(self):
        class DummyRepo(ThinkRepository):
            def get_think(self, message: str):
                return super().get_think(message)

        repository = DummyRepo()
        with pytest.raises(NotImplementedError):
            repository.get_think("Hello, world!")