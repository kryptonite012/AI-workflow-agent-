"""
Test suite for ModelManager model loading functionality
"""

import os
import subprocess
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.utils.model_manager import ModelManager
from src.config import settings


class TestModelManagerLoading(unittest.TestCase):
    def setUp(self):
        """Reset singleton instance before each test"""
        ModelManager.instance = None
        ModelManager.current_model = None

    def tearDown(self):
        """Clean up after each test"""
        ModelManager.instance = None
        ModelManager.current_model = None

    @patch("subprocess.Popen")
    def test_load_valid_model(self, mock_popen):
        """Test loading a valid model"""
        mock_process = MagicMock()
        mock_process.stdout.read.return_value.decode.return_value = ""
        mock_popen.return_value = mock_process

        ModelManager.load_model(settings.DEFAULT_MODEL)

        self.assertEqual(ModelManager.current_model, settings.DEFAULT_MODEL)
        mock_popen.assert_called_once_with(
            "ollama ps", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

    def test_load_invalid_model(self):
        """Test loading an invalid model raises ValueError"""
        with self.assertRaises(ValueError) as context:
            ModelManager.load_model("invalid_model")

        self.assertIn("Model invalid_model is not available", str(context.exception))
        self.assertIn("Available models:", str(context.exception))

    @patch("subprocess.Popen")
    def test_model_already_running_detection(self, mock_popen):
        """Test detection of already running model"""
        mock_process = MagicMock()
        # Simulate model already running
        mock_process.stdout.read.return_value.decode.return_value = f"NAME    ID    SIZE    PROCESSOR\n{settings.DEFAULT_MODEL}    abc123    4.1GB    100% GPU"
        mock_popen.return_value = mock_process

        ModelManager.load_model(settings.DEFAULT_MODEL)

        self.assertEqual(ModelManager.current_model, settings.DEFAULT_MODEL)

    @patch("subprocess.Popen")
    @patch("os.system")
    def test_model_switching(self, mock_os_system, mock_popen):
        """Test switching from one model to another"""
        mock_process = MagicMock()
        mock_process.stdout.read.return_value.decode.return_value = (
            f"{settings.DEFAULT_MODEL}"
        )
        mock_popen.return_value = mock_process

        # Load first model
        ModelManager.load_model(settings.DEFAULT_MODEL)
        self.assertEqual(ModelManager.current_model, settings.DEFAULT_MODEL)

        # Switch to second model
        mock_process.stdout.read.return_value.decode.return_value = (
            f"{settings.DEFAULT_MODEL}"
        )
        ModelManager.load_model(settings.CYPHER_MODEL)

        # Should stop previous model and load new one
        mock_os_system.assert_called_once_with(f"ollama stop {settings.DEFAULT_MODEL}")
        self.assertEqual(ModelManager.current_model, settings.CYPHER_MODEL)

    @patch("subprocess.Popen")
    def test_same_model_already_loaded(self, mock_popen):
        """Test loading the same model that's already loaded"""
        mock_process = MagicMock()
        mock_process.stdout.read.return_value.decode.return_value = (
            f"{settings.DEFAULT_MODEL}"
        )
        mock_popen.return_value = mock_process

        # Load model first time
        ModelManager.load_model(settings.DEFAULT_MODEL)

        # Try to load same model again; verify it doesn't crash and emits an 'already loaded' log
        with patch("src.ui.diagnostics.debug_helpers.debug_info") as mock_debug_info:
            ModelManager.load_model(settings.DEFAULT_MODEL)

            # We don't rely on exact formatting, just that the message indicates the condition.
            called_args = " ".join(str(a) for c in mock_debug_info.call_args_list for a in c.args)
            assert "already" in called_args.lower() and "loaded" in called_args.lower()

    @patch("os.system")
    def test_stop_model(self, mock_os_system):
        """Test stopping current model"""
        ModelManager.current_model = settings.DEFAULT_MODEL

        ModelManager._stop_model()

        mock_os_system.assert_called_once_with(f"ollama stop {settings.DEFAULT_MODEL}")

    def test_stop_model_no_current_model(self):
        """Test stopping model when no model is current"""
        ModelManager.current_model = None

        # Should not raise any exception
        ModelManager._stop_model()

    @patch("subprocess.Popen")
    def test_model_list_validation(self, mock_popen):
        """Test that model_list contains expected models"""
        expected_models = [
            settings.DEFAULT_MODEL,
            settings.CYPHER_MODEL,
            settings.CLASSIFIER_MODEL,
        ]

        self.assertEqual(ModelManager.model_list, expected_models)

        # Test each model can be loaded
        mock_process = MagicMock()
        mock_process.stdout.read.return_value.decode.return_value = ""
        mock_popen.return_value = mock_process

        for model in expected_models:
            ModelManager.current_model = None  # Reset
            ModelManager.load_model(model)
            self.assertEqual(ModelManager.current_model, model)


if __name__ == "__main__":
    unittest.main()
