import pytest
from unittest.mock import Mock
import time
import threading
from types import SimpleNamespace
from src.domain.ports.guanacos_repository import GuanacosRepository
from src.application.use_cases.guanacos_spits import GuanacosSpits


class TestGuanacoSpits:
    def test_should_start_workers_for_each_guanaco(self):
        guanacos_repository = Mock(spec=GuanacosRepository)
        worker_1 = SimpleNamespace(work=Mock(return_value=True), name="worker1")
        worker_2 = SimpleNamespace(work=Mock(return_value=True), name="worker2")
        guanacos_repository.get_guanacos.return_value = [worker_1, worker_2]

        guanacos_spits = GuanacosSpits(guanacos_repository, sleep_time=1)

        # Start workers and let them run briefly, then stop
        threading.Thread(target=lambda: (time.sleep(0.2), guanacos_spits.stop()), daemon=True).start()
        guanacos_spits.run()

        # Workers should have been called at least once
        assert worker_1.work.call_count >= 1
        assert worker_2.work.call_count >= 1

    def test_should_run_workers_in_parallel(self):
        guanacos_repository = Mock(spec=GuanacosRepository)

        # Create counters to track concurrent execution
        execution_counter = {"count": 0, "max_concurrent": 0}
        lock = threading.Lock()

        def concurrent_work():
            with lock:
                execution_counter["count"] += 1
                execution_counter["max_concurrent"] = max(
                    execution_counter["max_concurrent"],
                    execution_counter["count"]
                )

            time.sleep(0.1)  # Simulate work

            with lock:
                execution_counter["count"] -= 1

            return True

        worker_1 = SimpleNamespace(work=Mock(side_effect=concurrent_work), name="worker1")
        worker_2 = SimpleNamespace(work=Mock(side_effect=concurrent_work), name="worker2")

        guanacos_repository.get_guanacos.return_value = [worker_1, worker_2]
        guanacos_spits = GuanacosSpits(guanacos_repository, sleep_time=1)

        # Run for a brief period then stop
        threading.Thread(target=lambda: (time.sleep(0.3), guanacos_spits.stop()), daemon=True).start()
        guanacos_spits.run()

        # Should have detected concurrent execution
        assert execution_counter["max_concurrent"] >= 2, "Workers should run concurrently"

    def test_should_handle_empty_repository(self):
        guanacos_repository = Mock(spec=GuanacosRepository)
        guanacos_repository.get_guanacos.return_value = []

        guanacos_spits = GuanacosSpits(guanacos_repository, sleep_time=1)

        # Should complete without error
        guanacos_spits.run()

        assert len(guanacos_spits.get_running_workers()) == 0

    def test_should_stop_gracefully(self):
        guanacos_repository = Mock(spec=GuanacosRepository)
        worker = SimpleNamespace(work=Mock(return_value=True), name="test_worker")
        guanacos_repository.get_guanacos.return_value = [worker]

        guanacos_spits = GuanacosSpits(guanacos_repository, sleep_time=1)

        # Start and verify worker is running
        run_thread = threading.Thread(target=guanacos_spits.run, daemon=True)
        run_thread.start()
        time.sleep(0.15)  # Let it start

        assert len(guanacos_spits.get_running_workers()) == 1

        # Stop and verify workers are stopped
        guanacos_spits.stop()
        run_thread.join(timeout=1.0)  # Wait for run() to complete

        assert len(guanacos_spits.get_running_workers()) == 0

    def test_should_handle_keyboard_interrupt_in_run(self):
        guanacos_repository = Mock(spec=GuanacosRepository)
        worker = SimpleNamespace(work=Mock(return_value=True), name="test_worker")
        guanacos_repository.get_guanacos.return_value = [worker]

        guanacos_spits = GuanacosSpits(guanacos_repository, sleep_time=1)

        # Mock _wait_for_shutdown to raise KeyboardInterrupt
        def mock_wait():
            raise KeyboardInterrupt()
        guanacos_spits._wait_for_shutdown = mock_wait

        # Should handle KeyboardInterrupt gracefully
        guanacos_spits.run()  # Should not raise exception

    def test_should_handle_duplicate_worker_names(self):
        guanacos_repository = Mock(spec=GuanacosRepository)
        worker1 = SimpleNamespace(work=Mock(return_value=True), name="duplicate_name")
        worker2 = SimpleNamespace(work=Mock(return_value=True), name="duplicate_name")
        guanacos_repository.get_guanacos.return_value = [worker1, worker2]

        guanacos_spits = GuanacosSpits(guanacos_repository, sleep_time=1)

        # Call _start_all_workers directly to test duplicate handling
        guanacos_spits._start_all_workers()

        # Should only have one worker due to duplicate name
        assert len(guanacos_spits._workers) == 1

        # Clean up
        guanacos_spits._stop_all_workers()

    def test_should_handle_workers_stopping_naturally(self):
        guanacos_repository = Mock(spec=GuanacosRepository)
        worker = SimpleNamespace(work=Mock(return_value=True), name="test_worker")
        guanacos_repository.get_guanacos.return_value = [worker]

        guanacos_spits = GuanacosSpits(guanacos_repository, sleep_time=1)

        # Mock workers to stop naturally
        def mock_is_running():
            return False  # Workers stopped naturally

        # Start the run in a thread and mock workers stopping
        threading.Thread(target=guanacos_spits.run, daemon=True).start()
        time.sleep(0.1)  # Let it start

        # Mock all workers as stopped
        for worker in guanacos_spits._workers.values():
            worker.is_running = mock_is_running

        time.sleep(0.2)  # Let it detect stopped workers

    def test_should_handle_signal_with_unknown_signal_number(self):
        guanacos_spits = GuanacosSpits(Mock(), sleep_time=1)

        # Test signal handler with unknown signal
        guanacos_spits._signal_handler(999, None)

        assert guanacos_spits._shutdown_requested is True

    def test_should_check_specific_worker_running_status(self):
        guanacos_repository = Mock(spec=GuanacosRepository)
        worker = SimpleNamespace(work=Mock(return_value=True), name="test_worker")
        guanacos_repository.get_guanacos.return_value = [worker]

        guanacos_spits = GuanacosSpits(guanacos_repository, sleep_time=1)

        # Test with non-existent worker
        assert guanacos_spits.is_worker_running("non_existent") is False

        # Start worker and test
        threading.Thread(target=guanacos_spits.run, daemon=True).start()
        time.sleep(0.1)  # Let it start

        assert guanacos_spits.is_worker_running("test_worker") is True

        guanacos_spits.stop()
        time.sleep(0.1)  # Let it stop

    def test_should_handle_keyboard_interrupt_in_wait_for_shutdown(self):
        guanacos_repository = Mock(spec=GuanacosRepository)
        guanacos_spits = GuanacosSpits(guanacos_repository, sleep_time=1)

        # Add some workers first
        guanacos_spits._workers = {"test": Mock(is_running=Mock(return_value=True))}

        # Mock time.sleep to raise KeyboardInterrupt after first call
        original_sleep = time.sleep
        call_count = [0]

        def mock_sleep(duration):
            call_count[0] += 1
            if call_count[0] >= 2:  # Raise on second call
                raise KeyboardInterrupt()
            original_sleep(0.01)  # Short real sleep for first call

        import time as time_module
        time_module.sleep = mock_sleep

        try:
            # Should re-raise KeyboardInterrupt
            with pytest.raises(KeyboardInterrupt):
                guanacos_spits._wait_for_shutdown()
        finally:
            time_module.sleep = original_sleep

    def test_should_stop_all_workers_when_no_workers_exist(self):
        guanacos_spits = GuanacosSpits(Mock(), sleep_time=1)

        # Should handle gracefully when no workers exist
        guanacos_spits._stop_all_workers()  # Should not raise exception
