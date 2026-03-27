import json
import re
from domain.ports.think_repository import ThinkRepository, ModelComplexity, ModelSpecialty
from domain.entities.user import User
from infrastructure.repositories.zulip_bot_manager import ZulipBotManager
from infrastructure.repositories.http_think_repository import HttpThinkRepository
from domain.ports.guanacos_repository import GuanacosRepository
from typing import Optional, Dict, List
import sqlite3

class HRThinkRepository(ThinkRepository):
    """
    Parses natural language requests to create or delete bots 
    and uses the ZulipBotManager to execute the actions.
    """
    def __init__(self, guanacos_repository: Optional[GuanacosRepository] = None, nlp_engine: Optional[ThinkRepository] = None):
        self.nlp_engine = nlp_engine or HttpThinkRepository()
        self.bot_manager = ZulipBotManager()
        self.guanacos_repository = guanacos_repository

    def get_think(self, message: str, required_complexity: Optional[ModelComplexity] = None) -> str:
        effective_message = self._extract_current_message(message)
        effective_complexity = required_complexity or ModelComplexity.MEDIUM
        intent = self._detect_intent(effective_message)
        if intent == "NONE":
            return "Entiendo. Para administrar bots, pídeme explícitamente crear, eliminar o limpiar bots obsoletos."

        if intent == "CLEANUP":
            return self._cleanup_obsolete_bots()
        if intent == "LIST":
            return self._list_active_bots(user_question=effective_message, use_ai=True)

        prompt = (
            "You are a Human Resources Bot parsing an instruction. "
            "Extract the action from this set: CREATE, DELETE, LIST, CLEANUP, NONE. "
            "Extract the bot's standard name when it applies. "
            "If creating, also extract a short name (no spaces, lowercase). "
            "If deleting all bots, use bot_name='ALL' and short_name='ALL'. "
            "If asking for active bots, use action='LIST'. "
            "If asking to remove obsolete bots, use action='CLEANUP'. "
            "If no explicit management command exists, set action to 'NONE'. "
            "Respond ONLY with a JSON object with keys 'action', 'bot_name', and 'short_name'. "
            "Example 1: 'Crea un bot llamado Pez' -> {\"action\": \"CREATE\", \"bot_name\": \"Pez\", \"short_name\": \"pez\"} "
            "Example 2: 'Destruye al bot Juan Perez' -> {\"action\": \"DELETE\", \"bot_name\": \"Juan Perez\", \"short_name\": \"\"} "
            "Example 3: 'elimina todos los bots' -> {\"action\": \"DELETE\", \"bot_name\": \"ALL\", \"short_name\": \"ALL\"} "
            "Example 4: 'cuales bots hay activos' -> {\"action\": \"LIST\", \"bot_name\": \"\", \"short_name\": \"\"} "
            f"Text to parse: '{effective_message}'"
        )
        
        try:
            # Get NLP interpretation
            nlp_response = self.nlp_engine.get_think(prompt, required_complexity=effective_complexity)
            
            parsed_command = self._parse_command(effective_message, nlp_response, fallback_intent=intent)
            
            action = parsed_command.get("action", "").upper()
            bot_name = (parsed_command.get("bot_name", "") or "").strip()
            short_name = (parsed_command.get("short_name", "") or "").strip().lower()

            if action == "NONE":
                return "No detecté una orden explícita de crear o eliminar bots."
            if action == "LIST":
                return self._list_active_bots(user_question=effective_message, use_ai=True)
            if action == "CLEANUP":
                return self._cleanup_obsolete_bots()
            if "recursos humanos" in bot_name.lower():
                return "No puedo crear ni eliminar el bot de Recursos Humanos desde este canal."
            
            if action == "CREATE":
                if not bot_name or not short_name:
                    return "No pude entender el nombre o el nombre corto para el nuevo bot."
                # Note: creating a bot typically uses bot_type 1 (generic)
                bot_data = self.bot_manager.create_bot(full_name=bot_name, short_name=short_name)
                
                if self.guanacos_repository:
                    self.guanacos_repository.save_guanaco(
                        name=bot_name,
                        short_name=short_name,
                        email=bot_data["email"],
                        api_key=bot_data["api_key"],
                        bot_type="guanaco"
                    )
                    
                return f"El bot '{bot_name}' ha sido creado exitosamente con email {bot_data['email']}."
                
            elif action == "DELETE":
                if bot_name.upper() == "ALL" or short_name.upper() == "ALL" or "todos los bots" in effective_message.lower():
                    return self._delete_all_non_hr_bots()
                if not bot_name:
                    return "No pude entender qué bot debo destruir."
                
                email = self._find_bot_email_by_name(bot_name) or self._find_bot_email_by_short_name(short_name)
                if not email:
                    return f"No encontré un bot llamado '{bot_name}' para destruir."
                
                if self.guanacos_repository:
                    db_short_name = self._find_db_short_name(bot_name, short_name)
                    if db_short_name:
                        self.guanacos_repository.delete_guanaco(short_name=db_short_name)
                
                self.bot_manager.deactivate_bot(email)
                return f"El bot '{bot_name}' ha sido destruido."
                
            else:
                return "Comando no reconocido. Solo puedo crear o destruir bots."
                
        except RuntimeError as e:
            return f"No pude completar la operación: {str(e)}"
        except Exception:
            return "No pude interpretar bien la instrucción. Intenta con 'crea bot X' o 'elimina bot X'."

    def _extract_current_message(self, text: str) -> str:
        marker = "MENSAJE_ACTUAL:"
        raw = text or ""
        if marker not in raw:
            return raw
        current = raw.split(marker, 1)[1]
        # Trim possible trailing instruction block from contextual prompt wrapper.
        current = current.split("Usa el historial", 1)[0]
        return current.strip()

    def _extract_json(self, response: str) -> str:
        """Finds the first '{' and last '}' to extract JSON from the string."""
        start = response.find("{")
        end = response.rfind("}")
        if start != -1 and end != -1:
            return response[start:end+1]
        return response

    def _parse_command(self, original_message: str, nlp_response: str, fallback_intent: str) -> Dict[str, str]:
        try:
            json_str = self._extract_json(nlp_response)
            parsed = json.loads(json_str)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        # Lightweight fallback parser.
        bot_name = self._extract_bot_name_from_text(original_message)
        short_name = re.sub(r"[^a-z0-9-]+", "", bot_name.lower().replace(" ", "-")) if bot_name else ""
        return {
            "action": fallback_intent,
            "bot_name": bot_name,
            "short_name": short_name,
        }

    def _detect_intent(self, message: str) -> str:
        text = (message or "").lower()

        cleanup_keywords = ["obsoleto", "obsoletos", "limpia", "limpiar", "cleanup", "depura", "huérfano", "huerfano"]
        if any(k in text for k in cleanup_keywords):
            return "CLEANUP"
        list_keywords = [
            "activos", "activos?", "listar bots", "lista de bots", "qué bots", "que bots",
            "cuales bots", "cuáles bots", "cuantos bots", "cuántos bots", "responsabilidades",
            "roles", "que hacen", "qué hacen", "que hace", "qué hace", "bots hay"
        ]
        if any(k in text for k in list_keywords):
            return "LIST"

        create_keywords = ["crea", "crear", "agrega", "agregar", "nuevo bot", "new bot"]
        delete_keywords = ["elimina", "eliminar", "borra", "borrar", "destruye", "destruir", "deactivate", "desactivar"]

        if any(k in text for k in create_keywords):
            return "CREATE"
        if any(k in text for k in delete_keywords):
            return "DELETE"
        return "NONE"

    def _extract_bot_name_from_text(self, text: str) -> str:
        if not text:
            return ""
        patterns = [
            r"(?:bot llamado|bot named)\s+([a-zA-Z0-9 _-]+)",
            r"(?:elimina|borra|destruye)\s+(?:al\s+)?bot\s+([a-zA-Z0-9 _-]+)",
            r"(?:crea|crear)\s+(?:un\s+)?bot\s+([a-zA-Z0-9 _-]+)",
        ]
        for pattern in patterns:
            m = re.search(pattern, text, flags=re.IGNORECASE)
            if m:
                return m.group(1).strip(" .,!?:;")
        return ""

    def _list_active_bots(self, user_question: str = "", use_ai: bool = False) -> str:
        db_bots = self._get_db_bots()
        if not db_bots:
            return "No hay bots registrados en la base de datos."

        rows: List[str] = []
        lines_for_model: List[str] = []
        for b in db_bots:
            bot_type = b.get("bot_type")
            role = "administración de bots y gobierno del sistema" if bot_type == "hr" else "asistente general de conversación"
            rows.append(f"- {b.get('name')} ({b.get('short_name')}, tipo={bot_type}, rol={role})")
            lines_for_model.append(f"{b.get('name')} | short={b.get('short_name')} | type={bot_type} | role={role}")

        deterministic = "Bots activos en BD:\n" + "\n".join(rows)
        if not use_ai:
            return deterministic

        try:
            prompt = (
                "Eres un asistente de RRHH. Responde en español claro y breve. "
                "Usa solo la información entregada. "
                "Incluye: total de bots y responsabilidades por bot.\n"
                f"Pregunta del usuario: {user_question}\n"
                "Datos de bots:\n"
                + "\n".join(lines_for_model)
            )
            answer = self.nlp_engine.get_think(prompt, required_complexity=ModelComplexity.MEDIUM)
            answer = (answer or "").strip()
            if answer:
                return answer
        except Exception:
            pass
        return deterministic

    def _get_db_bots(self) -> List[Dict]:
        if not self.guanacos_repository or not hasattr(self.guanacos_repository, "db_manager"):
            return []
        with self.guanacos_repository.db_manager.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bots")
            return [dict(row) for row in cursor.fetchall()]

    def _find_db_short_name(self, bot_name: str, short_name: str) -> Optional[str]:
        bot_name_l = (bot_name or "").lower()
        short_name_l = (short_name or "").lower()
        for row in self._get_db_bots():
            row_name = (row.get("name") or "").lower()
            row_short = (row.get("short_name") or "").lower()
            if row_name == bot_name_l or (short_name_l and row_short == short_name_l):
                return row.get("short_name")
        return None

    def _find_bot_email_by_short_name(self, short_name: str) -> Optional[str]:
        if not short_name:
            return None
        users_response = self.bot_manager.client.get_users()
        if users_response.get("result") == "success":
            for member in users_response.get("members", []):
                if member.get("is_bot") is not True:
                    continue
                email_prefix = (member.get("email") or "").split("@")[0].lower()
                if email_prefix == short_name.lower() or email_prefix.startswith(f"{short_name.lower()}-"):
                    return member.get("email")
        return None

    def _cleanup_obsolete_bots(self) -> str:
        if not self.guanacos_repository:
            return "No tengo acceso al repositorio para limpiar bots obsoletos."

        db_bots = self._get_db_bots()
        db_emails = {(b.get("email") or "").lower() for b in db_bots}

        users_response = self.bot_manager.client.get_users()
        if users_response.get("result") != "success":
            return f"No pude consultar usuarios de Zulip: {users_response.get('msg')}"

        deactivated = 0
        skipped = 0
        for member in users_response.get("members", []):
            if member.get("is_bot") is not True:
                continue
            email = (member.get("email") or "").lower()
            if not email or email in db_emails:
                continue
            if "rh" in email.split("@")[0]:
                skipped += 1
                continue
            try:
                self.bot_manager.deactivate_bot(email)
                deactivated += 1
            except Exception:
                skipped += 1

        return f"Limpieza completada. Bots obsoletos desactivados: {deactivated}. Omitidos: {skipped}."

    def _delete_all_non_hr_bots(self) -> str:
        if not self.guanacos_repository:
            return "No tengo acceso al repositorio para eliminar bots."

        db_bots = self._get_db_bots()
        if not db_bots:
            return "No hay bots para eliminar."

        deleted = 0
        skipped = 0
        for bot in db_bots:
            if bot.get("bot_type") == "hr":
                skipped += 1
                continue
            email = bot.get("email") or ""
            short_name = bot.get("short_name") or ""
            try:
                if email:
                    self.bot_manager.deactivate_bot(email)
            except Exception:
                # Keep going; still clean DB side.
                pass
            try:
                if short_name:
                    self.guanacos_repository.delete_guanaco(short_name=short_name)
                deleted += 1
            except Exception:
                skipped += 1

        return f"Eliminación masiva completada. Eliminados: {deleted}. Omitidos: {skipped}."

    def _find_bot_email_by_name(self, full_name: str) -> Optional[str]:
        """Lookup bot email using the users list."""
        users_response = self.bot_manager.client.get_users()
        if users_response.get("result") == "success":
            for member in users_response.get("members", []):
                # Using lower() for case-insensitive match
                if member.get("is_bot") is not True:
                    continue
                if member.get("full_name", "").lower() == full_name.lower():
                    return member.get("email")
        return None
