from transformers import AutoModelForCausalLM, AutoTokenizer
import os
import torch


class ModelsHandler:
    def __init__(self):
        self.models = ["Qwen/Qwen3-1.7B"]
        self._model = None
        self._tokenizer = None
        self.list_all_the_availables_devices()

    def list_all_the_availables_devices(self):
        num_cuda = torch.cuda.device_count() if torch.cuda.is_available() else 0
        num_cpu = os.cpu_count() or 1
        has_mps = hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
        has_xpu = hasattr(torch, "xpu") and hasattr(torch.xpu, "is_available") and torch.xpu.is_available()
        has_rocm = getattr(torch.version, "hip", None) is not None
        print(f"Availables cuda GPUs: {num_cuda}")
        print(f"Availables cpu: {num_cpu}")
        print(f"Availables mps: {has_mps}")
        print(f"Availables xpu: {has_xpu}")
        print(f"Availables amd_rocm: {has_rocm}")

    def get_model(self, model_name: str) -> AutoModelForCausalLM:
        if self._model is None:
            try:
                self._model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")
            except Exception:
                self._model = AutoModelForCausalLM.from_pretrained(model_name)
                if torch.cuda.is_available():
                    self._model.to("cuda")
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    self._model.to("mps")
                elif hasattr(torch, "xpu") and hasattr(torch.xpu, "is_available") and torch.xpu.is_available():
                    self._model.to("xpu")
            self._model.eval()
        return self._model

    def generate_text(self, prompt: str) -> str:
        try:
            print(f"[DEBUG] Generating text for prompt: {prompt}")
            model_id = self.models[0]
            model = self.get_model(model_id)
            if self._tokenizer is None:
                self._tokenizer = AutoTokenizer.from_pretrained(model_id)

            # Clean HTML tags from prompt if present
            import re
            clean_prompt = re.sub(r'<[^>]+>', '', prompt).strip()
            if not clean_prompt:
                clean_prompt = "Hello"

            print(f"[DEBUG] Clean prompt: {clean_prompt}")
            inputs = self._tokenizer(clean_prompt, return_tensors="pt", max_length=512, truncation=True)
            device = (
                "cuda" if torch.cuda.is_available() else
                ("mps" if hasattr(torch.backends, "mps") and torch.backends.mps.is_available() else
                 ("xpu" if hasattr(torch, "xpu") and torch.xpu.is_available() else "cpu"))
            )
            if device != "cpu":
                inputs = {k: v.to(device) for k, v in inputs.items()}
            pad_token_id = (
                self._tokenizer.pad_token_id if self._tokenizer.pad_token_id is not None
                else self._tokenizer.eos_token_id
            )
            print("[DEBUG] Starting generation...")
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=32,  # Reduced for faster generation
                    do_sample=False,
                    pad_token_id=pad_token_id,
                )
            result = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
            print(f"[DEBUG] Generated result: {result}")
            return result
        except Exception as e:
            print(f"[ERROR] Generation failed: {e}")
            return "I apologize, I'm having trouble generating a response right now."