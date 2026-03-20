import re
from typing import List
from domain.entities.chat_message import ChatMessage
from domain.entities.channel import Channel


class ConversationContextBuilder:
    """
    Builds LLM prompts from recent channel history.
    Keeps context shaping isolated from domain orchestration.
    """

    def __init__(self, history_limit: int = 20):
        self.history_limit = history_limit

    def sanitize_content(self, content: str) -> str:
        text = re.sub(r"<[^>]+>", "", content or "")
        return re.sub(r"\s+", " ", text).strip()

    def dedupe_and_sort_messages(self, messages: List[ChatMessage]) -> List[ChatMessage]:
        by_id = {}
        for msg in messages or []:
            if hasattr(msg, "id"):
                by_id[msg.id] = msg

        ordered = list(by_id.values())
        ordered.sort(key=lambda m: (getattr(m, "created_at", None), getattr(m, "id", 0)))
        return ordered

    def build_prompt(self, channel: Channel, target_message: ChatMessage, ordered_messages: List[ChatMessage]) -> str:
        target_index = max(
            (idx for idx, msg in enumerate(ordered_messages) if msg.id == target_message.id),
            default=len(ordered_messages) - 1,
        )
        previous = ordered_messages[max(0, target_index - self.history_limit):target_index]

        lines = []
        for msg in previous:
            sender = getattr(getattr(msg, "sender", None), "name", "Unknown")
            content = self.sanitize_content(getattr(msg, "content", ""))
            if content:
                lines.append(f"{sender}: {content}")

        history_text = "\n".join(lines) if lines else "(sin historial previo relevante)"
        current_text = self.sanitize_content(target_message.content)
        channel_type = "mensaje directo" if str(channel.get_id()).startswith("pm:") else "canal"

        return (
            "Responde en español, de forma útil y concisa.\n"
            f"Tipo de conversación: {channel_type}\n"
            f"Tópico: {channel.get_topic()}\n"
            f"Historial reciente (hasta {self.history_limit} mensajes previos):\n"
            f"{history_text}\n\n"
            "MENSAJE_ACTUAL:\n"
            f"{current_text}\n\n"
            "Usa el historial para mantener contexto, pero responde específicamente al MENSAJE_ACTUAL."
        )
