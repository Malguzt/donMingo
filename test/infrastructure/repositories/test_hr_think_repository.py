import pytest
from unittest.mock import MagicMock
from infrastructure.repositories.hr_think_repository import HRThinkRepository

@pytest.fixture
def hr_think_repository():
    repo = HRThinkRepository()
    repo.nlp_engine = MagicMock()
    repo.bot_manager = MagicMock()
    return repo

def test_extract_json_success(hr_think_repository):
    response = "Aqui esta el JSON: {\"action\": \"CREATE\", \"bot_name\": \"Test Bot\", \"short_name\": \"test\"} Saludos!"
    json_str = hr_think_repository._extract_json(response)
    assert json_str == '{"action": "CREATE", "bot_name": "Test Bot", "short_name": "test"}'

def test_extract_json_no_json(hr_think_repository):
    response = "No entiendo el comando."
    json_str = hr_think_repository._extract_json(response)
    assert json_str == response

def test_get_think_create_bot_success(hr_think_repository):
    hr_think_repository.nlp_engine.get_think.return_value = '{"action": "CREATE", "bot_name": "Nuevo Bot", "short_name": "nuevo"}'
    
    response = hr_think_repository.get_think("Crea el bot Nuevo Bot")
    
    assert response == "El bot 'Nuevo Bot' ha sido creado exitosamente."
    hr_think_repository.bot_manager.create_bot.assert_called_once_with(full_name="Nuevo Bot", short_name="nuevo")

def test_get_think_create_bot_missing_info(hr_think_repository):
    hr_think_repository.nlp_engine.get_think.return_value = '{"action": "CREATE", "bot_name": "Nuevo Bot"}'
    
    response = hr_think_repository.get_think("Crea el bot Nuevo Bot")
    
    assert "No pude entender" in response
    hr_think_repository.bot_manager.create_bot.assert_not_called()

def test_get_think_delete_bot_success(hr_think_repository):
    hr_think_repository.nlp_engine.get_think.return_value = '{"action": "DELETE", "bot_name": "Bot Malo", "short_name": ""}'
    hr_think_repository._find_bot_email_by_name = MagicMock(return_value="botmalo@midominio.com")
    
    response = hr_think_repository.get_think("Destruye a Bot Malo")
    
    assert response == "El bot 'Bot Malo' ha sido destruido."
    hr_think_repository.bot_manager.deactivate_bot.assert_called_once_with("botmalo@midominio.com")

def test_get_think_delete_bot_not_found(hr_think_repository):
    hr_think_repository.nlp_engine.get_think.return_value = '{"action": "DELETE", "bot_name": "Inexistente", "short_name": ""}'
    hr_think_repository._find_bot_email_by_name = MagicMock(return_value=None)
    
    response = hr_think_repository.get_think("Elimina a Inexistente")
    
    assert "No encontré un bot llamado 'Inexistente'" in response
    hr_think_repository.bot_manager.deactivate_bot.assert_not_called()

def test_get_think_invalid_action(hr_think_repository):
    hr_think_repository.nlp_engine.get_think.return_value = '{"action": "UPDATE", "bot_name": "Pepe", "short_name": ""}'
    
    response = hr_think_repository.get_think("Actualiza a Pepe")
    
    assert "Comando no reconocido" in response

def test_get_think_nlp_error(hr_think_repository):
    hr_think_repository.nlp_engine.get_think.side_effect = Exception("Model down")
    
    response = hr_think_repository.get_think("Que tal")
    
    assert "Hubo un error interno" in response
