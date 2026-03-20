from domain.ports.chat_message_repository import ChatMessageRepository
from domain.entities.user import User
from domain.errors import MissingUserError, MissingRepositoryError
from domain.ports.think_repository import ThinkRepository
from application.services.should_respond_gate import ShouldRespondGate
from infrastructure.observability.metrics import (
    BOT_UNREAD_MESSAGES,
    MSGS_PROCESSED,
    THINK_DURATION,
)
import time
import re
from typing import List
from domain.entities.chat_message import ChatMessage

class Guanaco:
    CONTEXT_HISTORY_LIMIT = 20

    def __init__(self, name: str = None, user: User = None, chat_message_repository: ChatMessageRepository = None, think_repository: ThinkRepository = None):
        self.name = name
        self.user = user
        self.chat_message_repository = chat_message_repository
        self.think_repository = think_repository
        self._respond_gate = ShouldRespondGate()

    def _infer_role(self) -> str:
        think_repo_name = self.think_repository.__class__.__name__.lower() if self.think_repository else ""
        bot_name = (self.name or "").lower()
        if "hr" in think_repo_name or "recursos humanos" in bot_name:
            return "hr"
        return "general"

    def _sanitize_content(self, content: str) -> str:
        text = re.sub(r"<[^>]+>", "", content or "")
        return re.sub(r"\s+", " ", text).strip()

    def _get_deduped_messages(self, messages: List[ChatMessage]) -> List[ChatMessage]:
        by_id = {}
        for msg in messages or []:
            if hasattr(msg, "id"):
                by_id[msg.id] = msg
        ordered = list(by_id.values())
        ordered.sort(key=lambda m: (getattr(m, "created_at", None), getattr(m, "id", 0)))
        return ordered

    def _build_context_prompt(self, channel, target_message: ChatMessage, ordered_messages: List[ChatMessage]) -> str:
        target_index = max((idx for idx, m in enumerate(ordered_messages) if m.id == target_message.id), default=len(ordered_messages) - 1)
        previous = ordered_messages[max(0, target_index - self.CONTEXT_HISTORY_LIMIT):target_index]

        lines = []
        for msg in previous:
            sender = getattr(getattr(msg, "sender", None), "name", "Unknown")
            content = self._sanitize_content(getattr(msg, "content", ""))
            if content:
                lines.append(f"{sender}: {content}")

        history_text = "\n".join(lines) if lines else "(sin historial previo relevante)"
        current_text = self._sanitize_content(target_message.content)
        channel_type = "mensaje directo" if str(channel.get_id()).startswith("pm:") else "canal"

        return (
            "Responde en español, de forma útil y concisa.\n"
            f"Tipo de conversación: {channel_type}\n"
            f"Tópico: {channel.get_topic()}\n"
            f"Historial reciente (hasta {self.CONTEXT_HISTORY_LIMIT} mensajes previos):\n"
            f"{history_text}\n\n"
            "MENSAJE_ACTUAL:\n"
            f"{current_text}\n\n"
            "Usa el historial para mantener contexto, pero responde específicamente al MENSAJE_ACTUAL."
        )

    def work(self):
        """Process unread messages once. Returns True if work was performed, False otherwise."""
        bot_name = self.name or "unnamed"

        if self.user is None:
            raise MissingUserError("Cannot work without a user")
        
        if self.chat_message_repository is None:
            raise MissingRepositoryError("Cannot work without a chat message repository")
        
        if self.think_repository is None:
            raise MissingRepositoryError("Cannot work without a think repository")

        unread_count = 0
        try:
            channels = self.chat_message_repository.get_streams_with_unread_messages()
            # Flatten messages from all channels to count them
            all_messages = []
            for c in channels.values():
                all_messages.extend(c.get_messages())
            unread_count = len(all_messages)
        except Exception as e:
            print(f"[ERROR] {self.name} failed to fetch unread messages: {e}")
            return False

        BOT_UNREAD_MESSAGES.labels(bot_name=bot_name).set(unread_count)

        if not channels:
            print(f"[DEBUG] {self.name} found no unread messages")
            pass
        else:
            print(f"[DEBUG] {self.name} evaluating {unread_count} unread messages across {len(channels)} channels")

        work_performed = False
        
        for channel in channels.values():
            print(f"Channel: {channel}")
            try:
                ordered_messages = self._get_deduped_messages(channel.get_messages())
                if not ordered_messages:
                    continue
                last_message = ordered_messages[-1]
                if last_message.sender != self.user:
                    gate = self._respond_gate.decide(
                        bot_name=bot_name,
                        bot_role=self._infer_role(),
                        message_text=last_message.content,
                        channel_id=channel.get_id(),
                    )
                    if not gate.should_respond:
                        print(
                            f"[DEBUG] {self.name} skipped message "
                            f"(channel={channel.get_id()}, reason={gate.reason})"
                        )
                        continue

                    start_time = time.time()
                    
                    # Processing message
                    prompt = self._build_context_prompt(channel, last_message, ordered_messages)
                    response_text = self.think_repository.get_think(prompt)
                    channel.respond(response_text)
                    
                    # Record metrics
                    THINK_DURATION.labels(guanaco_name=bot_name).observe(time.time() - start_time)
                    MSGS_PROCESSED.labels(guanaco_name=bot_name).inc()
                    
                    work_performed = True
            except Exception as e:
                print(f"[ERROR] {self.name} failed processing channel '{channel.get_id()}': {e}")
                continue
        
        if work_performed:
            print(f"{self.name} has processed messages")
        
        return work_performed
