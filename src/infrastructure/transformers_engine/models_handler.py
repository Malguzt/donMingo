from transformers import AutoModelForCausalLM, AutoTokenizer
import os
import torch
import gc
import re
from typing import Optional, Dict, Any
from huggingface_hub import snapshot_download, hf_hub_download
from requests.exceptions import ConnectionError

from .hardware_profiler import HardwareProfiler
from .model_catalog import ModelCatalog, ModelComplexity
from .model_router import ModelRouter

class ModelsHandler:
    def __init__(self):
        self.profiler = HardwareProfiler(memory_margin_percent=0.20)
        self.catalog = ModelCatalog()
        self.router = ModelRouter(self.catalog)
        
        # Cache of loaded models and tokenizers (key: huggingface_id)
        self._loaded_models: Dict[str, AutoModelForCausalLM] = {}
        self._loaded_tokenizers: Dict[str, AutoTokenizer] = {}
        
        # Print profile on startup
        print("--- Hardware Profile ---")
        print(self.profiler.get_profile_summary())
        print("------------------------")

    def _free_memory(self):
        """Forces garbage collection and empties CUDA cache."""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
    def _unload_all_models(self):
        """Unloads all currently loaded models to free memory."""
        print("[DEBUG] Unloading all models to free memory...")
        self._loaded_models.clear()
        self._loaded_tokenizers.clear()
        self._free_memory()

    def get_model_and_tokenizer(self, huggingface_id: str, complexity: ModelComplexity):
        """Loads and returns the model and tokenizer, managing memory dynamically."""
        
        if huggingface_id in self._loaded_models:
            return self._loaded_models[huggingface_id], self._loaded_tokenizers[huggingface_id]
            
        # If we are loading a LARGE model, we likely need all memory. Let's proactively unload others.
        if complexity == ModelComplexity.LARGE:
            self._unload_all_models()
            
        print(f"[DEBUG] Ensuring model {huggingface_id} is downloaded locally...")
        try:
            # This checks the local cache and downloads only what is missing
            snapshot_download(
                repo_id=huggingface_id,
                local_files_only=False, # Allow downloading if not present
                resume_download=True
            )
            print(f"[DEBUG] Model {huggingface_id} is ready locally.")
        except Exception as e:
            print(f"[WARNING] Could not verify/download model {huggingface_id} from Hugging Face Hub. Proceeding with load attempt... Error: {e}")

        print(f"[DEBUG] Loading model: {huggingface_id}...")
        
        try:
            # We use device_map="auto" and max_memory based on our profiler
            max_memory = self.profiler.generate_max_memory_mapping()
            
            model = AutoModelForCausalLM.from_pretrained(
                huggingface_id,
                device_map="auto",
                max_memory=max_memory,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                low_cpu_mem_usage=True # Crucial for large models
            )
        except Exception as e:
            print(f"[WARNING] Failed to load with auto device map, falling back to basic loading. Error: {e}")
            model = AutoModelForCausalLM.from_pretrained(huggingface_id)
            if torch.cuda.is_available():
                model.to("cuda")
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                model.to("mps")
            elif hasattr(torch, "xpu") and hasattr(torch.xpu, "is_available") and torch.xpu.is_available():
                model.to("xpu")
                
        model.eval()
        tokenizer = AutoTokenizer.from_pretrained(huggingface_id)
        
        self._loaded_models[huggingface_id] = model
        self._loaded_tokenizers[huggingface_id] = tokenizer
        
        return model, tokenizer

    def generate_text(self, prompt: str, required_complexity: Optional[ModelComplexity] = None) -> str:
        try:
            print(f"[DEBUG] Routing prompt: {prompt}")
            
            # Use Router to decide which model to use
            model_def = self.router.route_prompt(prompt, required_complexity)
            print(f"[DEBUG] Selected model: {model_def.huggingface_id} (Complexity: {model_def.complexity.value}, Specialty: {model_def.specialty.value})")
            
            # Load model and tokenizer
            model, tokenizer = self.get_model_and_tokenizer(model_def.huggingface_id, model_def.complexity)
            
            clean_prompt = re.sub(r'<[^>]+>', '', prompt).strip()
            if not clean_prompt:
                clean_prompt = "Hello"
                
            inputs = tokenizer(clean_prompt, return_tensors="pt", max_length=512, truncation=True)
            
            # Move inputs to the device of the model's first parameter 
            # (since device_map="auto" might split the model, inputs must go to the first device)
            first_device = next(model.parameters()).device
            inputs = {k: v.to(first_device) for k, v in inputs.items()}
            
            pad_token_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
            
            print(f"[DEBUG] Starting generation...")
            # We allow more tokens for reasoning models
            max_tokens = 256 if model_def.complexity == ModelComplexity.LARGE else 64
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    do_sample=True, # Enable sampling for better responses
                    temperature=0.7,
                    pad_token_id=pad_token_id,
                )
            result = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
            
            # Make sure we free some memory space and caches after generation
            self._free_memory()
            
            return result.strip()
        except Exception as e:
            print(f"[ERROR] Generation failed: {e}")
            return "I apologize, I'm having trouble generating a response right now."