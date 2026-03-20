from transformers import AutoModelForCausalLM, AutoTokenizer
import os
import threading
import torch
import signal
import queue
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

# Optimize memory allocation to avoid fragmentation
os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"
import gc
import re
from typing import Optional, Dict, Any
from huggingface_hub import HfApi, snapshot_download, hf_hub_download
from requests.exceptions import ConnectionError
from contextlib import contextmanager
from functools import wraps

from .hardware_profiler import HardwareProfiler
from .model_catalog import ModelCatalog, ModelComplexity
from .model_router import ModelRouter
from .model_size_estimator import ModelMemoryPredictor
from infrastructure.observability.metrics import (
    MODEL_ACTIVE_REQUESTS,
    MODEL_CACHE_SIZE,
    MODEL_DOWNLOAD_DOWNLOADED_BYTES,
    MODEL_DOWNLOAD_EVENTS_TOTAL,
    MODEL_DOWNLOAD_FILES_COMPLETED,
    MODEL_DOWNLOAD_FILES_TOTAL,
    MODEL_DOWNLOAD_IN_PROGRESS,
    MODEL_DOWNLOAD_PROGRESS_PERCENT,
    MODEL_DOWNLOAD_STATUS_INFO,
    MODEL_DOWNLOAD_TOTAL_BYTES,
    MODEL_GENERATION_SECONDS,
    MODEL_LOADED_INFO,
    MODEL_LOAD_TOTAL,
    MODEL_SELECTION_TOTAL,
    NODE_NAME,
)

class TimeoutException(Exception):
    """Exception raised when an operation times out."""
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Operation timed out")

try:
    from transformers import BitsAndBytesConfig
    HAS_BNB = True
except ImportError as e:
    print(f"[WARNING] BitsAndBytesConfig not found in transformers: {e}")
    HAS_BNB = False

class ModelsHandler:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ModelsHandler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        # Protects model/tokenizer caches and shared metadata.
        self._cache_lock = threading.RLock()
        # One lock per compute device to allow concurrency across GPUs.
        self._device_locks: Dict[str, threading.Lock] = {}
        self._download_locks: Dict[str, threading.Lock] = {}
        self._model_load_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ModelLoader")
        
        self.profiler = HardwareProfiler(memory_margin_percent=0.20)  # Target ~80% utilization
        self.catalog = ModelCatalog()
        self.router = ModelRouter(self.catalog)
        self.predictor = ModelMemoryPredictor(catalog=self.catalog)
        
        # Cache of loaded models and tokenizers (key: huggingface_id)
        self._loaded_models: Dict[str, AutoModelForCausalLM] = {}
        self._loaded_tokenizers: Dict[str, AutoTokenizer] = {}
        self._loaded_model_devices: Dict[str, str] = {}
        self._loaded_model_estimates_gb: Dict[str, float] = {}
        
        # Preload flag
        self._preload_started = False
        self._preload_done = False
        
        # Print profile on startup
        print("--- Hardware Profile ---")
        print(self.profiler.get_profile_summary())
        print(f"BitsAndBytes (4-bit) support: {HAS_BNB}")
        print("------------------------")

    def _free_memory(self):
        """Forces garbage collection and empties CUDA cache."""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def _complexity_label_for_model(self, huggingface_id: str) -> str:
        for model_def in self.catalog.models:
            if model_def.huggingface_id == huggingface_id:
                return model_def.complexity.value
        return "unknown"

    def _infer_model_device(self, model: AutoModelForCausalLM) -> str:
        try:
            return str(next(model.parameters()).device)
        except Exception:
            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
            return "cpu"

    def _get_device_lock(self, device_label: str) -> threading.Lock:
        with self._cache_lock:
            if device_label not in self._device_locks:
                self._device_locks[device_label] = threading.Lock()
            return self._device_locks[device_label]

    def _get_download_lock(self, model_id: str) -> threading.Lock:
        with self._cache_lock:
            if model_id not in self._download_locks:
                self._download_locks[model_id] = threading.Lock()
            return self._download_locks[model_id]

    def _parse_cuda_index(self, device_label: str) -> Optional[int]:
        if not device_label.startswith("cuda"):
            return None
        parts = device_label.split(":")
        if len(parts) == 2 and parts[1].isdigit():
            return int(parts[1])
        return 0

    def _choose_target_device(self, estimated_needed_gb: float) -> str:
        if torch.cuda.is_available():
            gpu_info = self.profiler.get_gpu_vram_info()
            if not gpu_info:
                return "cuda:0"

            # Prefer GPU with fewer loaded models to spread across devices first.
            loaded_per_gpu: Dict[int, int] = {gpu_id: 0 for gpu_id in gpu_info.keys()}
            for _, dev in self._loaded_model_devices.items():
                idx = self._parse_cuda_index(dev)
                if idx is not None and idx in loaded_per_gpu:
                    loaded_per_gpu[idx] += 1

            candidates = []
            for gpu_id, info in gpu_info.items():
                safe_gb = info.get("safe_limit_gb", 0.0)
                free_gb = info.get("free_gb", 0.0)
                candidates.append((loaded_per_gpu[gpu_id], -safe_gb, -free_gb, gpu_id))

            candidates.sort()
            chosen_gpu_id = candidates[0][3]
            return f"cuda:{chosen_gpu_id}"

        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def _is_oom_error(self, error: Exception) -> bool:
        text = str(error).lower()
        return isinstance(error, torch.OutOfMemoryError) or "out of memory" in text or "cuda out of memory" in text

    def _set_download_progress(
        self,
        model_id: str,
        files_completed: int,
        files_total: int,
        downloaded_bytes: int,
        total_bytes: int,
    ) -> None:
        files_total_safe = max(files_total, 0)
        total_bytes_safe = max(total_bytes, 0)
        progress = 0.0
        if total_bytes_safe > 0:
            progress = min(100.0, (downloaded_bytes / total_bytes_safe) * 100.0)
        elif files_total_safe > 0:
            progress = min(100.0, (files_completed / files_total_safe) * 100.0)

        MODEL_DOWNLOAD_FILES_TOTAL.labels(model_id=model_id, node=NODE_NAME).set(files_total_safe)
        MODEL_DOWNLOAD_FILES_COMPLETED.labels(model_id=model_id, node=NODE_NAME).set(files_completed)
        MODEL_DOWNLOAD_TOTAL_BYTES.labels(model_id=model_id, node=NODE_NAME).set(total_bytes_safe)
        MODEL_DOWNLOAD_DOWNLOADED_BYTES.labels(model_id=model_id, node=NODE_NAME).set(downloaded_bytes)
        MODEL_DOWNLOAD_PROGRESS_PERCENT.labels(model_id=model_id, node=NODE_NAME).set(progress)

    def _set_download_status(self, model_id: str, current_status: str) -> None:
        for status in ("idle", "in_progress", "success", "error"):
            MODEL_DOWNLOAD_STATUS_INFO.labels(
                model_id=model_id,
                node=NODE_NAME,
                status=status,
            ).set(1 if status == current_status else 0)

    def _ensure_model_artifacts(self, model_id: str) -> None:
        """
        Ensure model artifacts are present locally and emit progress metrics.
        Progress is tracked by completed files (and bytes when metadata is available).
        """
        download_lock = self._get_download_lock(model_id)
        with download_lock:
            # Fast-path: everything is already local.
            try:
                snapshot_download(
                    repo_id=model_id,
                    local_files_only=True,
                    resume_download=True,
                )
                self._set_download_progress(model_id, files_completed=1, files_total=1, downloaded_bytes=1, total_bytes=1)
                MODEL_DOWNLOAD_IN_PROGRESS.labels(model_id=model_id, node=NODE_NAME).set(0)
                self._set_download_status(model_id, "success")
                MODEL_DOWNLOAD_EVENTS_TOTAL.labels(model_id=model_id, node=NODE_NAME, status="cache_hit").inc()
                return
            except Exception:
                pass

            MODEL_DOWNLOAD_EVENTS_TOTAL.labels(model_id=model_id, node=NODE_NAME, status="started").inc()
            MODEL_DOWNLOAD_IN_PROGRESS.labels(model_id=model_id, node=NODE_NAME).set(1)
            self._set_download_status(model_id, "in_progress")
            self._set_download_progress(model_id, files_completed=0, files_total=0, downloaded_bytes=0, total_bytes=0)

            api = HfApi()
            repo_files = []
            try:
                try:
                    model_info = api.model_info(repo_id=model_id, files_metadata=True)
                    repo_files = [f for f in (model_info.siblings or []) if getattr(f, "rfilename", None)]
                except Exception as metadata_err:
                    print(f"[WARNING] Could not fetch file metadata for {model_id}: {metadata_err}")

                if not repo_files:
                    # Fallback keeps behavior if metadata is unavailable.
                    snapshot_download(
                        repo_id=model_id,
                        local_files_only=False,
                        resume_download=True,
                    )
                    self._set_download_progress(model_id, files_completed=1, files_total=1, downloaded_bytes=1, total_bytes=1)
                    MODEL_DOWNLOAD_IN_PROGRESS.labels(model_id=model_id, node=NODE_NAME).set(0)
                    self._set_download_status(model_id, "success")
                    MODEL_DOWNLOAD_EVENTS_TOTAL.labels(model_id=model_id, node=NODE_NAME, status="success").inc()
                    return

                total_files = len(repo_files)
                total_bytes = sum(int(getattr(repo_file, "size", 0) or 0) for repo_file in repo_files)
                completed_files = 0
                downloaded_bytes = 0
                self._set_download_progress(
                    model_id=model_id,
                    files_completed=completed_files,
                    files_total=total_files,
                    downloaded_bytes=downloaded_bytes,
                    total_bytes=total_bytes,
                )

                for repo_file in repo_files:
                    filename = repo_file.rfilename
                    hf_hub_download(
                        repo_id=model_id,
                        filename=filename,
                        local_files_only=False,
                        resume_download=True,
                    )
                    completed_files += 1
                    downloaded_bytes += int(getattr(repo_file, "size", 0) or 0)
                    self._set_download_progress(
                        model_id=model_id,
                        files_completed=completed_files,
                        files_total=total_files,
                        downloaded_bytes=downloaded_bytes,
                        total_bytes=total_bytes,
                    )

                MODEL_DOWNLOAD_IN_PROGRESS.labels(model_id=model_id, node=NODE_NAME).set(0)
                self._set_download_status(model_id, "success")
                MODEL_DOWNLOAD_EVENTS_TOTAL.labels(model_id=model_id, node=NODE_NAME, status="success").inc()
            except Exception:
                MODEL_DOWNLOAD_IN_PROGRESS.labels(model_id=model_id, node=NODE_NAME).set(0)
                self._set_download_status(model_id, "error")
                MODEL_DOWNLOAD_EVENTS_TOTAL.labels(model_id=model_id, node=NODE_NAME, status="error").inc()
                raise
    
    def preload_models(self) -> None:
        """Preload all default models at startup in background."""
        if self._preload_started:
            return
        
        self._preload_started = True
        print("[INFO] Starting background model preload...")
        
        def _preload_worker():
            try:
                if torch.cuda.is_available() and torch.cuda.device_count() >= 2:
                    # Preload up to 2 medium models to keep both GPUs warm and utilized.
                    preload_candidates = [
                        ("Qwen/Qwen2.5-7B-Instruct", ModelComplexity.MEDIUM),
                        ("Qwen/Qwen2.5-Coder-7B", ModelComplexity.MEDIUM),
                    ]
                else:
                    preload_candidates = [
                        ("Qwen/Qwen2.5-1.5B-Instruct", ModelComplexity.SMALL),
                    ]

                success_count = 0
                for model_id, complexity in preload_candidates:
                    try:
                        print(f"[DEBUG] Preloading model: {model_id} ({complexity.value})")
                        self.get_model_and_tokenizer(model_id, complexity)
                        success_count += 1
                    except Exception as model_err:
                        print(f"[WARNING] Preload model failed ({model_id}): {model_err}")

                if success_count == 0 and torch.cuda.is_available():
                    # Last-resort fallback if medium preload failed.
                    try:
                        print("[WARNING] Falling back to SMALL preload due to previous failures...")
                        self.get_model_and_tokenizer("Qwen/Qwen2.5-1.5B-Instruct", ModelComplexity.SMALL)
                        success_count += 1
                    except Exception as fallback_err:
                        print(f"[ERROR] Fallback preload failed: {fallback_err}")

                print(f"[DEBUG] Model preload sequence completed. successful={success_count}")
                self._preload_done = True
            except Exception as e:
                print(f"[ERROR] Preload failed: {e}")
                self._preload_done = True  # Mark as done even if failed
        
        preload_thread = threading.Thread(target=_preload_worker, daemon=True, name="ModelPreloader")
        preload_thread.start()
            
    def _unload_all_models(self):
        """Unloads all currently loaded models to free memory."""
        print("[DEBUG] Unloading all models to free memory...")
        for model_id, device in self._loaded_model_devices.items():
            MODEL_LOADED_INFO.labels(
                model_id=model_id,
                complexity=self._complexity_label_for_model(model_id),
                device=device,
                node=NODE_NAME,
            ).set(0)
        self._loaded_models.clear()
        self._loaded_tokenizers.clear()
        self._loaded_model_devices.clear()
        self._loaded_model_estimates_gb.clear()
        MODEL_CACHE_SIZE.labels(node=NODE_NAME).set(0)
        self._free_memory()

    def get_model_and_tokenizer(self, huggingface_id: str, complexity: ModelComplexity):
        """Loads and returns the model and tokenizer, managing memory dynamically."""
        complexity_label = complexity.value if isinstance(complexity, ModelComplexity) else "unknown"

        with self._cache_lock:
            if huggingface_id in self._loaded_models:
                print(f"[DEBUG] Model {huggingface_id} already loaded in cache")
                cached_device = self._loaded_model_devices.get(
                    huggingface_id, self._infer_model_device(self._loaded_models[huggingface_id])
                )
                MODEL_LOADED_INFO.labels(
                    model_id=huggingface_id,
                    complexity=complexity_label,
                    device=cached_device,
                    node=NODE_NAME,
                ).set(1)
                MODEL_CACHE_SIZE.labels(node=NODE_NAME).set(len(self._loaded_models))
                MODEL_LOAD_TOTAL.labels(
                    model_id=huggingface_id,
                    complexity=complexity_label,
                    device=cached_device,
                    node=NODE_NAME,
                    status="cache_hit",
                ).inc()
                return self._loaded_models[huggingface_id], self._loaded_tokenizers[huggingface_id]
                
            # If we are loading a LARGE model, we likely need all memory. Let's proactively unload others.
            if complexity == ModelComplexity.LARGE:
                self._unload_all_models()
        
        print(f"[DEBUG] Ensuring model {huggingface_id} is downloaded locally...")
        
        # Memory Prediction Check
        available_vram = self.profiler.get_total_available_vram_gb()
        # We assume float16 for now as it's the default in our load logic
        estimated_needed = self.predictor.estimate_vram_required_gb(huggingface_id, target_dtype="float16")
        target_device = self._choose_target_device(estimated_needed)
        
        print(
            f"[INFO] Memory Check: {huggingface_id} needs ~{estimated_needed:.2f}GB. "
            f"Available VRAM (safe total): {available_vram:.2f}GB. Target device: {target_device}"
        )
        
        if estimated_needed > available_vram:
            print(f"[WARNING] Model {huggingface_id} is predicted to exceed available VRAM ({estimated_needed:.2f}GB > {available_vram:.2f}GB).")
            print(f"[TIP] Consider using a smaller model or installing 'bitsandbytes' for 4-bit quantization.")
        
        # Ensure model artifacts are available and expose progress metrics.
        try:
            print(f"[DEBUG] Downloading model artifacts (if needed)...")
            self._ensure_model_artifacts(huggingface_id)
            print(f"[DEBUG] Model {huggingface_id} is ready locally.")
        except ConnectionError as e:
            MODEL_DOWNLOAD_IN_PROGRESS.labels(model_id=huggingface_id, node=NODE_NAME).set(0)
            print(f"[WARNING] Connection error while downloading {huggingface_id}: {e}")
            print(f"[INFO] Attempting local-cache fallback...")
            try:
                snapshot_download(
                    repo_id=huggingface_id,
                    local_files_only=True,
                    resume_download=True,
                )
                self._set_download_progress(huggingface_id, files_completed=1, files_total=1, downloaded_bytes=1, total_bytes=1)
                self._set_download_status(huggingface_id, "success")
                MODEL_DOWNLOAD_EVENTS_TOTAL.labels(model_id=huggingface_id, node=NODE_NAME, status="fallback_local").inc()
            except Exception:
                self._set_download_status(huggingface_id, "error")
        except Exception as e:
            MODEL_DOWNLOAD_IN_PROGRESS.labels(model_id=huggingface_id, node=NODE_NAME).set(0)
            print(f"[WARNING] Could not verify/download model {huggingface_id}. Error: {e}")
            print(f"[INFO] Attempting local-cache fallback...")
            try:
                snapshot_download(
                    repo_id=huggingface_id,
                    local_files_only=True,
                    resume_download=True,
                )
                self._set_download_progress(huggingface_id, files_completed=1, files_total=1, downloaded_bytes=1, total_bytes=1)
                self._set_download_status(huggingface_id, "success")
                MODEL_DOWNLOAD_EVENTS_TOTAL.labels(model_id=huggingface_id, node=NODE_NAME, status="fallback_local").inc()
            except Exception:
                self._set_download_status(huggingface_id, "error")

        print(f"[DEBUG] Loading model: {huggingface_id}...")
        model_device = target_device

        used_auto_device_map = False
        try:
            # Start with simple load kwargs without device_map to avoid hanging
            load_kwargs = {
                "low_cpu_mem_usage": True,
                "torch_dtype": torch.float16 if torch.cuda.is_available() else torch.float32
            }
            
            # Use 4-bit only when the chosen GPU safe budget would be exceeded.
            use_4bit = False
            target_gpu_idx = self._parse_cuda_index(target_device) if target_device.startswith("cuda") else None
            if HAS_BNB and target_gpu_idx is not None:
                gpu_info = self.profiler.get_gpu_vram_info().get(target_gpu_idx, {})
                safe_gb = gpu_info.get("safe_limit_gb", 0.0)
                if estimated_needed > safe_gb and safe_gb > 0:
                    use_4bit = True

            if use_4bit:
                print(f"[DEBUG] Loading with 4-bit quantization (bitsandbytes) due to VRAM budget...")
                load_kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                )

            # For medium/large models on constrained GPUs, prefer HF auto sharding/offload.
            if torch.cuda.is_available() and complexity in (ModelComplexity.MEDIUM, ModelComplexity.LARGE):
                load_kwargs["device_map"] = "auto"
                load_kwargs["max_memory"] = self.profiler.generate_max_memory_mapping()
                load_kwargs["offload_folder"] = "/tmp/donmingo-offload"
                load_kwargs["offload_state_dict"] = True
                used_auto_device_map = True

            print(f"[DEBUG] Calling AutoModelForCausalLM.from_pretrained() with kwargs: {load_kwargs}")
            model = AutoModelForCausalLM.from_pretrained(
                huggingface_id,
                **load_kwargs
            )
            print(f"[DEBUG] Model loading completed, moving to device...")
            
            # If Transformers already distributed/offloaded, do not force a full .to(cuda:X).
            if used_auto_device_map or getattr(model, "hf_device_map", None):
                model_device = "auto"
            # Move model to chosen device.
            elif target_device.startswith("cuda"):
                gpu_idx = self._parse_cuda_index(target_device) or 0
                print(f"[DEBUG] Moving model to CUDA device {gpu_idx}...")
                torch.cuda.set_device(gpu_idx)
                model.to(torch.device(f"cuda:{gpu_idx}"))
                model_device = f"cuda:{gpu_idx}"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                print(f"[DEBUG] Moving model to MPS...")
                model.to("mps")
                model_device = "mps"
            else:
                print(f"[DEBUG] No accelerator available, keeping model on CPU")
                model_device = "cpu"

        except Exception as e:
            # Emergency retry path for OOM: aggressive offload and (if available) 4-bit quantization.
            if self._is_oom_error(e) and torch.cuda.is_available():
                print(f"[WARNING] OOM loading {huggingface_id}. Retrying with emergency offload strategy...")
                self._unload_all_models()
                self._free_memory()
                emergency_kwargs = {
                    "low_cpu_mem_usage": True,
                    "torch_dtype": torch.float16,
                    "device_map": "auto",
                    "max_memory": self.profiler.generate_max_memory_mapping(),
                    "offload_folder": "/tmp/donmingo-offload",
                    "offload_state_dict": True,
                }
                if HAS_BNB:
                    emergency_kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_use_double_quant=True,
                    )
                try:
                    model = AutoModelForCausalLM.from_pretrained(huggingface_id, **emergency_kwargs)
                    tokenizer = AutoTokenizer.from_pretrained(huggingface_id)
                    model.eval()
                    with self._cache_lock:
                        self._loaded_models[huggingface_id] = model
                        self._loaded_tokenizers[huggingface_id] = tokenizer
                        self._loaded_model_devices[huggingface_id] = "auto"
                        self._loaded_model_estimates_gb[huggingface_id] = estimated_needed
                    MODEL_LOADED_INFO.labels(
                        model_id=huggingface_id,
                        complexity=complexity_label,
                        device="auto",
                        node=NODE_NAME,
                    ).set(1)
                    MODEL_CACHE_SIZE.labels(node=NODE_NAME).set(len(self._loaded_models))
                    MODEL_LOAD_TOTAL.labels(
                        model_id=huggingface_id,
                        complexity=complexity_label,
                        device="auto",
                        node=NODE_NAME,
                        status="success",
                    ).inc()
                    print(f"[INFO] Emergency offload load succeeded for {huggingface_id}")
                    return model, tokenizer
                except Exception as retry_error:
                    e = retry_error
            MODEL_LOAD_TOTAL.labels(
                model_id=huggingface_id,
                complexity=complexity_label,
                device=model_device,
                node=NODE_NAME,
                status="error",
            ).inc()
            print(f"[ERROR] Failed to load model {huggingface_id}: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        print(f"[DEBUG] Setting model to eval mode...")
        model.eval()
        
        print(f"[DEBUG] Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(huggingface_id)
        print(f"[DEBUG] Tokenizer loaded")
        
        with self._cache_lock:
            self._loaded_models[huggingface_id] = model
            self._loaded_tokenizers[huggingface_id] = tokenizer
            self._loaded_model_devices[huggingface_id] = model_device
            self._loaded_model_estimates_gb[huggingface_id] = estimated_needed

        MODEL_LOADED_INFO.labels(
            model_id=huggingface_id,
            complexity=complexity_label,
            device=model_device,
            node=NODE_NAME,
        ).set(1)
        MODEL_CACHE_SIZE.labels(node=NODE_NAME).set(len(self._loaded_models))
        MODEL_LOAD_TOTAL.labels(
            model_id=huggingface_id,
            complexity=complexity_label,
            device=model_device,
            node=NODE_NAME,
            status="success",
        ).inc()

        print(f"[DEBUG] Model and tokenizer cached")
        return model, tokenizer

    def generate_text(self, prompt: str, required_complexity: Optional[ModelComplexity] = None) -> str:
        """
        Generate text using the appropriate model.
        Uses a per-device lock to allow parallel generation across multiple GPUs.
        """
        print(f"[DEBUG] generate_text() called")
        selected_model_id = None
        selected_complexity = "unknown"
        generation_started_at = None
        generation_status = "error"
        active_request_incremented = False
        device_lock = None
        lock_acquired = False
        try:
            print(f"[DEBUG] Routing prompt: {prompt}")
            
            # Use Router to decide which model to use
            model_def = self.router.route_prompt(prompt, required_complexity)
            print(f"[DEBUG] Selected model: {model_def.huggingface_id} (Complexity: {model_def.complexity.value}, Specialty: {model_def.specialty.value})")
            selected_model_id = model_def.huggingface_id
            selected_complexity = model_def.complexity.value
            generation_started_at = time.perf_counter()
            MODEL_SELECTION_TOTAL.labels(
                model_id=selected_model_id,
                complexity=selected_complexity,
                specialty=model_def.specialty.value,
            ).inc()
            
            # Load model and tokenizer with timeout protection
            print(f"[DEBUG] Calling get_model_and_tokenizer...")
            try:
                model, tokenizer = self.get_model_and_tokenizer(model_def.huggingface_id, model_def.complexity)
            except Exception as load_error:
                if self._is_oom_error(load_error) and model_def.complexity != ModelComplexity.SMALL:
                    fallback_model = self.catalog.find_best_model(ModelComplexity.SMALL, model_def.specialty)
                    if fallback_model is None:
                        fallback_model = self.catalog.get_default_model()
                    print(
                        f"[WARNING] OOM with {model_def.huggingface_id}. "
                        f"Falling back to {fallback_model.huggingface_id}."
                    )
                    selected_model_id = fallback_model.huggingface_id
                    selected_complexity = fallback_model.complexity.value
                    MODEL_SELECTION_TOTAL.labels(
                        model_id=selected_model_id,
                        complexity=selected_complexity,
                        specialty=fallback_model.specialty.value,
                    ).inc()
                    model, tokenizer = self.get_model_and_tokenizer(fallback_model.huggingface_id, fallback_model.complexity)
                else:
                    raise
            MODEL_ACTIVE_REQUESTS.labels(
                model_id=selected_model_id,
                complexity=selected_complexity,
            ).inc()
            active_request_incremented = True
            print(f"[DEBUG] Model loaded successfully")

            model_device_label = self._infer_model_device(model)
            device_lock = self._get_device_lock(model_device_label)
            lock_acquired = device_lock.acquire(timeout=8)
            if not lock_acquired:
                generation_status = "timeout"
                print(f"[WARNING] Device {model_device_label} is busy.")
                return "I apologize, the selected model device is busy. Please try again."
            
            clean_prompt = re.sub(r'<[^>]+>', '', prompt).strip()
            if not clean_prompt:
                clean_prompt = "Hello"
            
            print(f"[DEBUG] Tokenizing input...")
            inputs = tokenizer(clean_prompt, return_tensors="pt", max_length=512, truncation=True)
            print(f"[DEBUG] Tokenization complete, input shape: {inputs['input_ids'].shape}")
            
            # Move inputs to the same device as the loaded model.
            try:
                target_torch_device = next(model.parameters()).device
            except Exception:
                target_torch_device = torch.device("cpu")
            inputs = {k: v.to(target_torch_device) for k, v in inputs.items()}
            print(f"[DEBUG] Inputs moved to {target_torch_device}")
            
            pad_token_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
            
            print(f"[DEBUG] Starting generation...")
            # We allow more tokens for reasoning models
            max_tokens = 40 if model_def.complexity == ModelComplexity.LARGE else 32
            
            with torch.no_grad():
                print(f"[DEBUG] Calling model.generate with max_tokens={max_tokens}...")
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    do_sample=True, # Enable sampling for better responses
                    temperature=0.7,
                    pad_token_id=pad_token_id,
                )
                print(f"[DEBUG] Generation completed, outputs shape: {outputs.shape}")
            
            print(f"[DEBUG] Decoding output...")
            result = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
            print(f"[DEBUG] Decoding complete, result length: {len(result)}")
            
            # Make sure we free some memory space and caches after generation
            self._free_memory()
            generation_status = "success"
            
            return result.strip()
        except TimeoutException as e:
            generation_status = "timeout"
            print(f"[ERROR] Operation timed out: {e}")
            return "I apologize, the operation took too long. Please try again."
        except Exception as e:
            generation_status = "error"
            print(f"[ERROR] Generation failed: {e}")
            import traceback
            traceback.print_exc()
            return "I apologize, I'm having trouble generating a response right now."
        finally:
            if lock_acquired and device_lock is not None:
                device_lock.release()
            if selected_model_id and generation_started_at is not None:
                elapsed = time.perf_counter() - generation_started_at
                MODEL_GENERATION_SECONDS.labels(
                    model_id=selected_model_id,
                    complexity=selected_complexity,
                    status=generation_status,
                ).observe(elapsed)
                if active_request_incremented:
                    MODEL_ACTIVE_REQUESTS.labels(
                        model_id=selected_model_id,
                        complexity=selected_complexity,
                    ).dec()
