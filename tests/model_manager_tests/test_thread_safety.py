"""
Advanced thread safety tests for ModelManager
"""

import concurrent.futures
import os
import sys
import threading
import time
import unittest
from unittest.mock import patch, MagicMock

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.utils.model_manager import ModelManager
from src.config import settings


class TestModelManagerThreadSafety(unittest.TestCase):
    def setUp(self):
        """Reset singleton instance before each test"""
        ModelManager.instance = None
        ModelManager.current_model = None

    def tearDown(self):
        """Clean up after each test"""
        ModelManager.instance = None
        ModelManager.current_model = None

    @patch("subprocess.Popen")
    def test_concurrent_instance_creation(self, mock_popen):
        """Test concurrent instance creation with multiple threads"""
        mock_process = MagicMock()
        mock_process.stdout.read.return_value.decode.return_value = ""
        mock_popen.return_value = mock_process

        instances = []
        exceptions = []

        def create_instance(thread_id):
            try:
                instance = ModelManager(model=settings.DEFAULT_MODEL)
                instances.append((thread_id, instance))
            except Exception as e:
                exceptions.append((thread_id, e))

        # Create many threads simultaneously
        threads = []
        num_threads = 20

        for i in range(num_threads):
            thread = threading.Thread(target=create_instance, args=(i,))
            threads.append(thread)

        # Start all threads at roughly the same time
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        self.assertEqual(len(exceptions), 0, f"Exceptions occurred: {exceptions}")
        self.assertEqual(len(instances), num_threads)

        # All instances should be the same object
        first_instance = instances[0][1]
        for thread_id, instance in instances:
            self.assertIs(
                instance, first_instance, f"Thread {thread_id} got different instance"
            )

    @patch("subprocess.Popen")
    @patch("os.system")
    def test_concurrent_model_loading(self, mock_os_system, mock_popen):
        """Test concurrent model loading operations"""
        mock_process = MagicMock()
        mock_process.stdout.read.return_value.decode.return_value = ""
        mock_popen.return_value = mock_process

        results = []
        exceptions = []

        def load_model_worker(model_name, thread_id):
            try:
                ModelManager.load_model(model_name)
                results.append((thread_id, model_name, ModelManager.current_model))
            except Exception as e:
                exceptions.append((thread_id, e))

        # Test concurrent loading of different models
        models_to_test = [
            settings.DEFAULT_MODEL,
            settings.CYPHER_MODEL,
            settings.CLASSIFIER_MODEL,
        ]

        threads = []
        for i, model in enumerate(models_to_test * 3):  # Test each model multiple times
            thread = threading.Thread(target=load_model_worker, args=(model, i))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Check that no exceptions occurred
        self.assertEqual(len(exceptions), 0, f"Exceptions occurred: {exceptions}")

        # Current model should be one of the valid models
        self.assertIn(ModelManager.current_model, ModelManager.model_list)

    @patch("subprocess.Popen")
    def test_race_condition_singleton_creation(self, mock_popen):
        """Test for race conditions in singleton creation"""
        mock_process = MagicMock()
        mock_process.stdout.read.return_value.decode.return_value = ""
        mock_popen.return_value = mock_process

        # Use a barrier to synchronize thread start
        barrier = threading.Barrier(10)
        instances = []

        def create_with_barrier():
            barrier.wait()  # Wait for all threads to be ready
            instance = ModelManager(model=settings.DEFAULT_MODEL)
            instances.append(instance)

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_with_barrier)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All instances should be identical
        first_instance = instances[0]
        for instance in instances[1:]:
            self.assertIs(instance, first_instance)

    @patch("subprocess.Popen")
    def test_thread_pool_executor(self, mock_popen):
        """Test ModelManager with ThreadPoolExecutor"""
        mock_process = MagicMock()
        mock_process.stdout.read.return_value.decode.return_value = ""
        mock_popen.return_value = mock_process

        def get_manager_instance():
            return ModelManager(model=settings.DEFAULT_MODEL)

        # Use ThreadPoolExecutor to create instances
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(get_manager_instance) for _ in range(10)]
            instances = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # All instances should be the same
        first_instance = instances[0]
        for instance in instances[1:]:
            self.assertIs(instance, first_instance)

    @patch("subprocess.Popen")
    @patch("os.system")
    def test_model_switching_thread_safety(self, mock_os_system, mock_popen):
        """Test thread safety during model switching"""
        mock_process = MagicMock()
        mock_process.stdout.read.return_value.decode.return_value = settings.DEFAULT_MODEL
        mock_popen.return_value = mock_process

        switch_results = []

        def switch_model_repeatedly(thread_id):
            models = [
                settings.DEFAULT_MODEL,
                settings.CYPHER_MODEL,
                settings.CLASSIFIER_MODEL,
            ]
            for i in range(5):
                model = models[i % len(models)]
                ModelManager.load_model(model)
                switch_results.append((thread_id, i, model, ModelManager.current_model))
                time.sleep(0.01)  # Small delay to increase chance of race conditions

        threads = []
        for i in range(3):
            thread = threading.Thread(target=switch_model_repeatedly, args=(i,))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Verify that current_model is always a valid model
        for thread_id, iteration, requested_model, actual_model in switch_results:
            self.assertIn(
                actual_model,
                ModelManager.model_list,
                f"Thread {thread_id}, iteration {iteration}: invalid current_model {actual_model}",
            )

    @patch("subprocess.Popen")
    def test_class_variable_consistency(self, mock_popen):
        """Test that class variables remain consistent across threads"""
        mock_process = MagicMock()
        mock_process.stdout.read.return_value.decode.return_value = ""
        mock_popen.return_value = mock_process

        class_var_snapshots = []

        def capture_class_vars(thread_id):
            manager = ModelManager(model=settings.DEFAULT_MODEL)
            snapshot = {
                "thread_id": thread_id,
                "instance_id": id(manager),
                "current_model": ModelManager.current_model,
                "model_list": ModelManager.model_list.copy(),
                "instance_is_none": ModelManager.instance is None,
            }
            class_var_snapshots.append(snapshot)

        threads = []
        for i in range(8):
            thread = threading.Thread(target=capture_class_vars, args=(i,))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All snapshots should show consistent class variables
        first_snapshot = class_var_snapshots[0]
        for snapshot in class_var_snapshots[1:]:
            self.assertEqual(snapshot["instance_id"], first_snapshot["instance_id"])
            self.assertEqual(snapshot["current_model"], first_snapshot["current_model"])
            self.assertEqual(snapshot["model_list"], first_snapshot["model_list"])
            self.assertFalse(snapshot["instance_is_none"])


if __name__ == "__main__":
    unittest.main()
