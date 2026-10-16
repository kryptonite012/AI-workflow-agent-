"""
Test suite for ModelManager error handling scenarios
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


class TestModelManagerErrorHandling(unittest.TestCase):
    def setUp(self):
        """Reset singleton instance before each test"""
        ModelManager.instance = None
        ModelManager.current_model = None

    def tearDown(self):
        """Clean up after each test"""
        ModelManager.instance = None
        ModelManager.current_model = None

    def test_invalid_model_name(self):
        """Test error handling for invalid model names"""
        invalid_models = ["nonexistent_model", "", None, 123, [], {}]

        for invalid_model in invalid_models:
            with self.subTest(model=invalid_model):
                with self.assertRaises((ValueError, TypeError)):
                    ModelManager.load_model(invalid_model)

    @patch("subprocess.Popen")
    def test_subprocess_error_handling(self, mock_popen):
        """Test handling of subprocess errors"""
        # Simulate subprocess error
        mock_popen.side_effect = subprocess.CalledProcessError(1, "ollama ps")

        with self.assertRaises(subprocess.CalledProcessError):
            ModelManager.load_model(settings.DEFAULT_MODEL)

    @patch("subprocess.Popen")
    def test_subprocess_timeout_handling(self, mock_popen):
        """Test handling of subprocess timeout"""
        # Simulate subprocess timeout
        mock_popen.side_effect = subprocess.TimeoutExpired("ollama ps", 30)

        with self.assertRaises(subprocess.TimeoutExpired):
            ModelManager.load_model(settings.DEFAULT_MODEL)

    @patch("subprocess.Popen")
    def test_malformed_ollama_ps_output(self, mock_popen):
        """Test handling of malformed ollama ps output"""
        mock_process = MagicMock()
        # Simulate malformed output
        mock_process.stdout.read.return_value.decode.return_value = (
            "corrupted output\x00\xff"
        )
        mock_popen.return_value = mock_process

        # Should not crash, should handle gracefully
        try:
            ModelManager.load_model(settings.DEFAULT_MODEL)
            self.assertEqual(ModelManager.current_model, settings.DEFAULT_MODEL)
        except Exception as e:
            self.fail(f"Should handle malformed output gracefully, but raised: {e}")

    @patch("subprocess.Popen")
    def test_empty_ollama_ps_output(self, mock_popen):
        """Test handling of empty ollama ps output"""
        mock_process = MagicMock()
        mock_process.stdout.read.return_value.decode.return_value = ""
        mock_popen.return_value = mock_process

        ModelManager.load_model(settings.DEFAULT_MODEL)
        self.assertEqual(ModelManager.current_model, settings.DEFAULT_MODEL)

    @patch("os.system")
    def test_stop_model_system_error(self, mock_os_system):
        """Test error handling when stopping model fails"""
        # Simulate system command failure
        mock_os_system.return_value = 1  # Non-zero exit code

        ModelManager.current_model = settings.DEFAULT_MODEL

        # Should not raise exception even if stop command fails
        try:
            ModelManager._stop_model()
        except Exception as e:
            self.fail(
                f"_stop_model should handle system errors gracefully, but raised: {e}"
            )

    @patch("subprocess.Popen")
    def test_unicode_handling_in_output(self, mock_popen):
        """Test handling of unicode characters in ollama ps output"""
        mock_process = MagicMock()
        # Include unicode characters
        mock_process.stdout.read.return_value.decode.return_value = (
            f"模型 {settings.DEFAULT_MODEL} 正在运行"
        )
        mock_popen.return_value = mock_process

        try:
            ModelManager.load_model(settings.DEFAULT_MODEL)
            self.assertEqual(ModelManager.current_model, settings.DEFAULT_MODEL)
        except UnicodeError as e:
            self.fail(f"Should handle unicode characters gracefully, but raised: {e}")

    @patch("subprocess.Popen")
    def test_large_output_handling(self, mock_popen):
        """Test handling of very large ollama ps output"""
        mock_process = MagicMock()
        # Simulate very large output
        large_output = "x" * 10000 + settings.DEFAULT_MODEL + "y" * 10000
        mock_process.stdout.read.return_value.decode.return_value = large_output
        mock_popen.return_value = mock_process

        ModelManager.load_model(settings.DEFAULT_MODEL)
        self.assertEqual(ModelManager.current_model, settings.DEFAULT_MODEL)

    @patch("subprocess.Popen")
    def test_model_list_modification_protection(self, mock_popen):
        """Test that model_list can be modified but validation still works"""
        mock_process = MagicMock()
        mock_process.stdout.read.return_value.decode.return_value = ""
        mock_popen.return_value = mock_process

        original_model_list = ModelManager.model_list.copy()

        # Try to modify model_list externally
        ModelManager.model_list.append("malicious_model")

        # Since the list is mutable, the new model should now be valid
        # This test shows that the model_list is not protected (which is the current behavior)
        try:
            ModelManager.load_model("malicious_model")
            # If we get here, the model was accepted (current behavior)
            self.assertIn("malicious_model", ModelManager.model_list)
        except ValueError:
            # If we get here, the model was rejected (would be better behavior)
            self.fail("Model validation should accept models in the current model_list")

        # Restore original list for other tests
        ModelManager.model_list = original_model_list


if __name__ == "__main__":
    unittest.main()
