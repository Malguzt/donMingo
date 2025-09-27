"""
Use case for managing multiple Guanaco workers with infinite loop execution.
Follows Clean Architecture principles by orchestrating domain entities through repositories.
"""

import signal
import threading
from typing import List, Dict

from domain.ports.guanacos_repository import GuanacosRepository
from infrastructure.workers.guanaco_worker import GuanacoWorker  # Added this import


class GuanacosSpits:
    """
    Use case for managing multiple Guanaco workers.
    Coordinates the execution of multiple Guanacos concurrently with proper lifecycle management.
    """
    
    def __init__(self, guanacos_repository: GuanacosRepository, sleep_time: int = 10):
        self.guanacos_repository = guanacos_repository
        self.sleep_time = sleep_time
        self._workers: Dict[str, GuanacoWorker] = {}  # Removed quotes around GuanacoWorker
        self._shutdown_requested = False
        
        # Set up signal handlers for graceful shutdown
        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

    def run(self) -> None:
        """
        Main entry point that starts all Guanaco workers and keeps them running.
        Blocks until shutdown is requested via signal or stop() method.
        """
        try:
            guanacos = self.guanacos_repository.get_guanacos()
            if not guanacos:
                print("[WARNING] No guanacos found in repository")
                return
            
            for guanaco in guanacos:
                guanaco.work()

        except KeyboardInterrupt:
            print("\n[INFO] Shutdown requested via keyboard interrupt")
        finally:
            pass
    
    def stop(self) -> None:
        """Request shutdown of all workers."""
        self._shutdown_requested = True
    
    def _start_all_workers(self) -> None:
        """Initialize and start workers for all Guanacos from the repository."""
        pass
    
    def _stop_all_workers(self) -> None:
        """Stop all running workers gracefully."""
        pass
    
    def _wait_for_shutdown(self) -> None:
        """Wait for shutdown signal or until all workers stop."""
        pass
    
    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals gracefully."""
        signal_names = {signal.SIGINT: "SIGINT", signal.SIGTERM: "SIGTERM"}
        signal_name = signal_names.get(signum, f"Signal {signum}")
        print(f"\n[INFO] Received {signal_name}, initiating graceful shutdown...")
        self._shutdown_requested = True
    
    def get_running_workers(self) -> List[str]:
        """Get list of currently running worker IDs."""
        return [worker_id for worker_id, worker in self._workers.items() 
                if worker.is_running()]
    
    def is_worker_running(self, worker_id: str) -> bool:
        """Check if a specific worker is running."""
        if worker_id not in self._workers:
            return False
        return self._workers[worker_id].is_running()