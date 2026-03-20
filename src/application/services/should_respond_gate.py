import os
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class GateDecision:
    should_respond: bool
    reason: str


class CpuBinaryDecider:
    """
    Optional tiny CPU decider.
    Returns True/False when it can classify, None on failure.
    """

    def __init__(self):
        self._enabled = os.getenv("ENABLE_CPU_GATE_MODEL", "0") == "1"
        self._model_id = os.getenv("CPU_GATE_MODEL_ID", "Qwen/Qwen2.5-0.5B-Instruct")
        self._loaded = False
        self._tokenizer = None
        self._model = None

    def _ensure_loaded(self) -> bool:
        if not self._enabled:
            return False
        if self._loaded:
            return self._model is not None and self._tokenizer is not None
        self._loaded = True
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(self._model_id)
            self._model = AutoModelForCausalLM.from_pretrained(
                self._model_id,
                low_cpu_mem_usage=True,
                torch_dtype=torch.float32,
            )
            self._model.to("cpu")
            self._model.eval()
            return True
        except Exception:
            self._tokenizer = None
            self._model = None
            return False

    def decide(self, bot_role: str, bot_name: str, message: str) -> Optional[bool]:
        if not self._ensure_loaded():
            return None
        try:
            import torch

            prompt = (
                "You are a binary routing classifier.\n"
                "Answer ONLY YES or NO.\n"
                f"Bot role: {bot_role}\n"
                f"Bot name: {bot_name}\n"
                f"Message: {message}\n"
                "Should this bot respond?"
            )
            inputs = self._tokenizer(prompt, return_tensors="pt", truncation=True, max_length=256)
            with torch.no_grad():
                output = self._model.generate(
                    **inputs,
                    max_new_tokens=3,
                    do_sample=False,
                    temperature=0.0,
                    pad_token_id=self._tokenizer.eos_token_id,
                )
            text = self._tokenizer.decode(output[0], skip_special_tokens=True).upper()
            if "YES" in text:
                return True
            if "NO" in text:
                return False
            return None
        except Exception:
            return None


class ShouldRespondGate:
    """
    First decision node in the bot graph.
    Stage 1: hard rules (cheap).
    Stage 2: role taxonomy rules (cheap).
    Stage 3: optional tiny CPU binary model.
    """

    def __init__(self):
        self._cpu_decider = CpuBinaryDecider()

    def decide(
        self,
        *,
        bot_name: str,
        bot_role: str,
        message_text: str,
        channel_id: str,
    ) -> GateDecision:
        text = (message_text or "").strip()
        channel = (channel_id or "").strip()
        bot_name_l = (bot_name or "").lower()
        text_l = text.lower()
        is_dm = channel.startswith("pm:")

        if not text:
            return GateDecision(False, "empty_message")

        # Stage 1: direct messages always considered relevant.
        if is_dm:
            return GateDecision(True, "direct_message")

        # Stage 2: fast mention check.
        if bot_name_l and bot_name_l in text_l:
            return GateDecision(True, "mentioned_by_name")

        # Stage 2b: role taxonomy.
        if bot_role == "hr":
            hr_keywords = [
                "crear bot", "crea bot", "agregar bot", "eliminar bot", "borra bot",
                "destruye bot", "limpiar bots", "bots obsoletos", "recursos humanos",
            ]
            if any(k in text_l for k in hr_keywords):
                return GateDecision(True, "hr_intent_keyword")
            return GateDecision(False, "hr_not_relevant")

        # Generic bots: only respond when there is clear signal.
        signal_keywords = ["ayuda", "help", "explica", "qué", "que", "como", "cómo", "?"]
        if any(k in text_l for k in signal_keywords):
            return GateDecision(True, "generic_signal_keyword")

        # Stage 3: optional tiny CPU model.
        cpu_vote = self._cpu_decider.decide(bot_role=bot_role, bot_name=bot_name, message=text)
        if cpu_vote is True:
            return GateDecision(True, "cpu_binary_yes")
        if cpu_vote is False:
            return GateDecision(False, "cpu_binary_no")

        return GateDecision(False, "default_not_relevant")

