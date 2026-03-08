import psutil
import torch
from typing import Dict, Any

class HardwareProfiler:
    """Profiles system hardware to determine memory constraints for model loading."""

    def __init__(self, memory_margin_percent: float = 0.20):
        """
        Args:
            memory_margin_percent: Float representing the percentage of memory to leave free
                                   (e.g., 0.20 means use up to 80% of available memory).
        """
        self.memory_margin_percent = memory_margin_percent

    def get_system_ram_info(self) -> Dict[str, float]:
        """Returns system RAM info in GB."""
        vm = psutil.virtual_memory()
        return {
            "total_gb": vm.total / (1024 ** 3),
            "available_gb": vm.available / (1024 ** 3),
            "safe_limit_gb": (vm.available / (1024 ** 3)) * (1.0 - self.memory_margin_percent)
        }

    def get_gpu_vram_info(self) -> Dict[int, Dict[str, float]]:
        """Returns vRAM info per GPU in GB."""
        gpu_info = {}
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                total_memory = torch.cuda.get_device_properties(i).total_memory
                allocated_memory = torch.cuda.memory_allocated(i)
                free_memory = total_memory - allocated_memory
                gpu_info[i] = {
                    "total_gb": total_memory / (1024 ** 3),
                    "free_gb": free_memory / (1024 ** 3),
                    "safe_limit_gb": (free_memory / (1024 ** 3)) * (1.0 - self.memory_margin_percent)
                }
        return gpu_info

    def generate_max_memory_mapping(self) -> Dict[Any, str]:
        """
        Generates the max_memory dictionary required by HuggingFace's from_pretrained
        to bound memory usage on GPUs and CPU.
        """
        max_memory: Dict[Any, str] = {}
        
        # Add GPU limits
        gpu_info = self.get_gpu_vram_info()
        for gpu_id, info in gpu_info.items():
            # Format expected by HF: e.g., "10GiB"
            # Using integer GiB to be safe and conservative
            safe_limit = max(1, int(info["safe_limit_gb"]))
            max_memory[gpu_id] = f"{safe_limit}GiB"
        
        # Add CPU RAM limit
        ram_info = self.get_system_ram_info()
        safe_ram_limit = max(1, int(ram_info["safe_limit_gb"]))
        max_memory["cpu"] = f"{safe_ram_limit}GiB"
        
        return max_memory

    def get_profile_summary(self) -> str:
        """Returns a string summary of the hardware profile."""
        ram = self.get_system_ram_info()
        gpus = self.get_gpu_vram_info()
        
        summary = [f"System RAM: {ram['available_gb']:.2f}GB / {ram['total_gb']:.2f}GB (Safe limit: {ram['safe_limit_gb']:.2f}GB)"]
        if gpus:
            for gpu_id, info in gpus.items():
                name = torch.cuda.get_device_name(gpu_id)
                summary.append(f"GPU {gpu_id} ({name}): Free {info['free_gb']:.2f}GB / Total {info['total_gb']:.2f}GB (Safe limit: {info['safe_limit_gb']:.2f}GB)")
        else:
            summary.append("No CUDA GPUs detected.")
            
        return "\n".join(summary)
