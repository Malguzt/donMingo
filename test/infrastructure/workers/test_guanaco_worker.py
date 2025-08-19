import pytest
import time
import threading
from unittest.mock import Mock
from types import SimpleNamespace
from infrastructure.workers.guanaco_worker import GuanacoWorker
from domain.entities.guanaco.guanaco import Guanaco


class TestGuanacoWorker:
    def test_should_start_and_stop_worker(self):
        guanaco = Mock(spec=Guanaco)
        guanaco.work.return_value = True
        guanaco.name = "test_guanaco"
        
        worker = GuanacoWorker(guanaco, sleep_time=0.1)
        
        worker.start()
        assert worker.is_running()
        
        worker.stop()
        assert not worker.is_running()
    
    def test_should_execute_guanaco_work_repeatedly(self):
        guanaco = Mock(spec=Guanaco)
        guanaco.work.return_value = True
        guanaco.name = "test_guanaco"
        
        worker = GuanacoWorker(guanaco, sleep_time=0.1)
        
        worker.start()
        time.sleep(0.3)  # Let it run a few cycles
        worker.stop()
        
        assert guanaco.work.call_count >= 2
    
    def test_should_raise_error_when_starting_already_running_worker(self):
        guanaco = Mock(spec=Guanaco)
        guanaco.work.return_value = True
        guanaco.name = "test_guanaco"
        
        worker = GuanacoWorker(guanaco, sleep_time=0.1)
        
        worker.start()
        
        with pytest.raises(ValueError, match="Worker for test_guanaco is already running"):
            worker.start()
        
        worker.stop()
    
    def test_should_handle_guanaco_work_exceptions(self):
        guanaco = Mock(spec=Guanaco)
        guanaco.work.side_effect = Exception("Test error")
        guanaco.name = "test_guanaco"
        
        worker = GuanacoWorker(guanaco, sleep_time=0.1)
        
        # Should not raise exception, but worker should stop
        worker.start()
        time.sleep(0.2)  # Give it time to encounter the error
        
        # Worker should have stopped due to exception
        assert not worker.is_running()
    
    def test_should_stop_gracefully_when_not_running(self):
        guanaco = Mock(spec=Guanaco)
        guanaco.name = "test_guanaco"
        
        worker = GuanacoWorker(guanaco, sleep_time=0.1)
        
        # Should not raise exception when stopping a worker that's not running
        worker.stop()
        assert not worker.is_running()
    
    def test_should_use_guanaco_name_in_thread_name(self):
        guanaco = Mock(spec=Guanaco)
        guanaco.work.return_value = True
        guanaco.name = "my_special_guanaco"
        
        worker = GuanacoWorker(guanaco, sleep_time=0.1)
        
        worker.start()
        
        # Check that the thread name includes the guanaco name
        assert worker._worker_thread.name == "GuanacoWorker-my_special_guanaco"
        
        worker.stop()

    def test_should_handle_stop_when_worker_thread_is_none(self):
        guanaco = Mock(spec=Guanaco)
        guanaco.name = "test_guanaco"
        
        worker = GuanacoWorker(guanaco, sleep_time=0.1)
        
        # Manually set thread to None to test the branch
        worker._worker_thread = None
        worker._is_running = True
        
        # Should handle gracefully when worker thread is None
        worker.stop()
        assert not worker.is_running()
