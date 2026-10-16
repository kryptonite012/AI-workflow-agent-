"""
Test suite for ModelManager singleton behavior
"""

import os
import sys
import threading
import unittest
from unittest.mock import patch, MagicMock

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.utils.model_manager import ModelManager
from src.config import settings


class TestModelManagerSingleton(unittest.TestCase):
    def setUp(self):
        """Reset singleton instance before each test"""
        ModelManager.instance = None
        ModelManager.current_model = None

    def tearDown(self):
        """Clean up after each test"""
        ModelManager.instance = None
        ModelManager.current_model = None

    @patch("subprocess.Popen")
    def test_singleton_instance_creation(self, mock_popen):
        """Test that only one instance is created"""
        # Mock subprocess call
        mock_process = MagicMock()
        mock_process.stdout.read.return_value.decode.return_value = ""
        mock_popen.return_value = mock_process

        # Create first instance
        manager1 = ModelManager(model=settings.DEFAULT_MODEL)

        # Create second instance
        manager2 = ModelManager(model=settings.DEFAULT_MODEL)

        # Both should be the same instance
        self.assertIs(manager1, manager2)
        self.assertEqual(id(manager1), id(manager2))

    @patch("subprocess.Popen")
    def test_singleton_across_different_parameters(self, mock_popen):
        """Test singleton behavior with different initialization parameters"""
        mock_process = MagicMock()
        mock_process.stdout.read.return_value.decode.return_value = ""
        mock_popen.return_value = mock_process

        manager1 = ModelManager(model=settings.DEFAULT_MODEL)
        manager2 = ModelManager(model=settings.CYPHER_MODEL)

        self.assertIs(manager1, manager2)

    @patch("subprocess.Popen")
    def test_thread_safety_basic(self, mock_popen):
        """Basic thread safety test for singleton creation"""
        mock_process = MagicMock()
        mock_process.stdout.read.return_value.decode.return_value = ""
        mock_popen.return_value = mock_process

        instances = []

        def create_instance():
            instance = ModelManager(model=settings.DEFAULT_MODEL)
            instances.append(instance)

        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_instance)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All instances should be the same
        first_instance = instances[0]
        for instance in instances[1:]:
            self.assertIs(first_instance, instance)


if __name__ == "__main__":
    unittest.main()
