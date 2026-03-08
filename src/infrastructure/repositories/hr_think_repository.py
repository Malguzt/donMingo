import json
from domain.ports.think_repository import ThinkRepository
from domain.entities.user import User
from infrastructure.repositories.zulip_bot_manager import ZulipBotManager
from infrastructure.repositories.transformers_think_repository import TransformersThinkRepository
from infrastructure.transformers_engine.model_catalog import ModelComplexity
from typing import Optional

class HRThinkRepository(ThinkRepository):
    """
    Parses natural language requests to create or delete bots 
    and uses the ZulipBotManager to execute the actions.
    """
    def __init__(self):
        self.nlp_engine = TransformersThinkRepository()
        self.bot_manager = ZulipBotManager()

    def get_think(self, message: str, required_complexity: ModelComplexity = ModelComplexity.MEDIUM) -> str:
        prompt = (
            "You are a Human Resources Bot parsing an instruction. "
            "Extract the action (either 'CREATE' or 'DELETE') and the bot's standard name from the following text. "
            "If creating, also extract a short name (no spaces, lowercase). "
            "Respond ONLY with a JSON object with keys 'action', 'bot_name', and 'short_name'. "
            "Example 1: 'Crea un bot llamado Pez' -> {\"action\": \"CREATE\", \"bot_name\": \"Pez\", \"short_name\": \"pez\"} "
            "Example 2: 'Destruye al bot Juan Perez' -> {\"action\": \"DELETE\", \"bot_name\": \"Juan Perez\", \"short_name\": \"\"} "
            f"Text to parse: '{message}'"
        )
        
        try:
            # Get NLP interpretation
            nlp_response = self.nlp_engine.get_think(prompt, required_complexity=required_complexity)
            
            # Extract JSON from response (in case the model adds extra text)
            json_str = self._extract_json(nlp_response)
            parsed_command = json.loads(json_str)
            
            action = parsed_command.get("action", "").upper()
            bot_name = parsed_command.get("bot_name", "")
            short_name = parsed_command.get("short_name", "")
            
            if action == "CREATE":
                if not bot_name or not short_name:
                    return "No pude entender el nombre o el nombre corto para el nuevo bot."
                # Note: creating a bot typically uses bot_type 1 (generic)
                self.bot_manager.create_bot(full_name=bot_name, short_name=short_name)
                return f"El bot '{bot_name}' ha sido creado exitosamente."
                
            elif action == "DELETE":
                if not bot_name:
                    return "No pude entender qué bot debo destruir."
                
                # We need the email to delete. We can derive it or search for the user by name.
                # Since Zulip requires email for deactivation, let's look it up.
                email = self._find_bot_email_by_name(bot_name)
                if not email:
                    return f"No encontré un bot llamado '{bot_name}' para destruir."
                
                self.bot_manager.deactivate_bot(email)
                return f"El bot '{bot_name}' ha sido destruido."
                
            else:
                return "Comando no reconocido. Solo puedo crear o destruir bots."
                
        except Exception as e:
            return f"Hubo un error interno procesando la solicitud: {str(e)}"

    def _extract_json(self, response: str) -> str:
        """Finds the first '{' and last '}' to extract JSON from the string."""
        start = response.find("{")
        end = response.rfind("}")
        if start != -1 and end != -1:
            return response[start:end+1]
        return response

    def _find_bot_email_by_name(self, full_name: str) -> Optional[str]:
        """Lookup bot email using the users list."""
        users_response = self.bot_manager.client.get_users()
        if users_response.get("result") == "success":
            for member in users_response.get("members", []):
                # Using lower() for case-insensitive match
                if member.get("full_name", "").lower() == full_name.lower():
                    return member.get("email")
        return None
