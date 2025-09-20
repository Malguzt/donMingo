import pytest
from domain.ports.guanacos_repository import GuanacosRepository

class TestGuanacosRepository:
    def test_should_rais_not_implemented_error_when_calling_get_guanacos(self):
        class DummyRepo(GuanacosRepository):
            def get_guanacos(self):
                return super().get_guanacos()

        repository = DummyRepo()
        with pytest.raises(NotImplementedError):
            repository.get_guanacos()
