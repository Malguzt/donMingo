"""
Infrastructure worker that manages a single Guanaco's execution in an infinite loop.
Handles technical concerns like threading, process lifecycle, and execution management.
"""

import time
import threading
from typing import Optional
from domain.entities.guanaco.guanaco import Guanaco
from infrastructure.observability.metrics import (
    BOT_WORKER_ERRORS_TOTAL,
    BOT_WORKER_LOOP_TOTAL,
    BOT_WORKER_UP,
)


class GuanacoWorker:
    """
    Infrastructure worker that manages a single Guanaco's execution in an infinite loop.
    Handles threading, process lifecycle, and other technical execution concerns.
    
    This belongs in the infrastructure layer because it deals with:
    - Threading and concurrency management
    - Process lifecycle control
    - Platform-specific execution details
    - Technical infrastructure concerns
    """
    
    def __init__(self, guanaco: Guanaco, sleep_time: int = 10):
        self.guanaco = guanaco
        self.sleep_time = sleep_time
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._is_running = False
    
    def start(self) -> None:
        """Start the worker in a separate thread."""
        if self._is_running:
            raise ValueError(f"Worker for {self.guanaco.name} is already running")

        bot_name = self.guanaco.name or "unnamed"
        self._stop_event.clear()
        self._worker_thread = threading.Thread(
            target=self._work_loop,
            name=f"GuanacoWorker-{self.guanaco.name or 'unnamed'}",
            daemon=True
        )
        self._worker_thread.start()
        self._is_running = True
        BOT_WORKER_UP.labels(bot_name=bot_name).set(1)
        print(f"[INFO] Guanaco worker '{self.guanaco.name}' started")
    
    def stop(self) -> None:
        """Stop the worker gracefully."""
        if not self._is_running:
            return

        bot_name = self.guanaco.name or "unnamed"
        self._stop_event.set()
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)

        self._is_running = False
        BOT_WORKER_UP.labels(bot_name=bot_name).set(0)
        print(f"[INFO] Guanaco worker '{self.guanaco.name}' stopped")
    
    def is_running(self) -> bool:
        """Check if the worker is currently running."""
        return self._is_running and self._worker_thread and self._worker_thread.is_alive()
    
    def _work_loop(self) -> None:
        """Main work loop that executes continuously until stopped."""
        bot_name = self.guanaco.name or "unnamed"
        try:
            while not self._stop_event.is_set():
                BOT_WORKER_LOOP_TOTAL.labels(bot_name=bot_name).inc()
                self.guanaco.work()
                
                # Sleep in small intervals to allow for responsive shutdown
                elapsed = 0
                while elapsed < self.sleep_time and not self._stop_event.is_set():
                    time.sleep(min(1, self.sleep_time - elapsed))
                    elapsed += 1
                    
        except Exception as e:
            BOT_WORKER_ERRORS_TOTAL.labels(bot_name=bot_name).inc()
            print(f"[ERROR] Guanaco worker '{self.guanaco.name}' encountered an error: {e}")
        finally:
            self._is_running = False
            BOT_WORKER_UP.labels(bot_name=bot_name).set(0)
