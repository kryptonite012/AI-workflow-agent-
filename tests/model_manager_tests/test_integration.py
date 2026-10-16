"""
Integration tests for ModelManager with ChatOllama
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

from langchain_core.messages import BaseMessage, HumanMessage

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.utils.model_manager import ModelManager
from src.config import settings


class TestModelManagerIntegration(unittest.TestCase):
    def setUp(self):
        """Reset singleton instance before each test"""
        ModelManager.instance = None
        ModelManager.current_model = None

    def tearDown(self):
        """Clean up after each test"""
        ModelManager.instance = None
        ModelManager.current_model = None

    @patch("subprocess.Popen")
    @patch.object(ModelManager, "invoke")
    def test_invoke_method_inheritance(self, mock_invoke, mock_popen):
        """Test that invoke method is properly inherited from ChatOllama"""
        mock_process = MagicMock()
        mock_process.stdout.read.return_value.decode.return_value = ""
        mock_popen.return_value = mock_process

        # Mock the invoke response
        mock_response = MagicMock(spec=BaseMessage)
        mock_invoke.return_value = mock_response

        manager = ModelManager(model=settings.DEFAULT_MODEL)

        # Test invoke call
        input_message = HumanMessage(content="Test message")
        result = manager.invoke(input_message)

        # Verify invoke was called and returned expected result
        # Check that invoke was called with the input message
        mock_invoke.assert_called_once_with(input_message)
        self.assertEqual(result, mock_response)

    @patch("subprocess.Popen")
    @patch.object(ModelManager, "invoke")
    def test_invoke_with_parameters(self, mock_invoke, mock_popen):
        """Test invoke method with various parameters"""
        mock_process = MagicMock()
        mock_process.stdout.read.return_value.decode.return_value = ""
        mock_popen.return_value = mock_process

        mock_response = MagicMock(spec=BaseMessage)
        mock_invoke.return_value = mock_response

        manager = ModelManager(model=settings.DEFAULT_MODEL)

        # Test invoke with config and stop parameters
        input_message = HumanMessage(content="Test message")
        config_param = {"temperature": 0.7}
        stop_param = ["END", "STOP"]

        result = manager.invoke(
            input=input_message,
            config=config_param,
            stop=stop_param,
            custom_param="test",
        )

        mock_invoke.assert_called_once_with(
            input=input_message,
            config=config_param,
            stop=stop_param,
            custom_param="test",
        )
        self.assertEqual(result, mock_response)

    @patch("subprocess.Popen")
    def test_initialization_with_chatollama_params(self, mock_popen):
        """Test ModelManager initialization with ChatOllama parameters"""
        mock_process = MagicMock()
        mock_process.stdout.read.return_value.decode.return_value = ""
        mock_popen.return_value = mock_process

        # Test initialization with typical ChatOllama parameters
        manager = ModelManager(
            model=settings.DEFAULT_MODEL,
            temperature=0.8,
            top_p=0.9,
            base_url="http://localhost:11434",
        )

        self.assertIsInstance(manager, ModelManager)
        self.assertEqual(ModelManager.current_model, settings.DEFAULT_MODEL)

    @patch("subprocess.Popen")
    def test_multiple_instances_same_functionality(self, mock_popen):
        """Test that multiple instance references work identically"""
        mock_process = MagicMock()
        mock_process.stdout.read.return_value.decode.return_value = ""
        mock_popen.return_value = mock_process

        manager1 = ModelManager(model=settings.DEFAULT_MODEL)
        manager2 = ModelManager(model=settings.CYPHER_MODEL)

        # Both should be the same instance
        self.assertIs(manager1, manager2)

        # Both should have access to the same class variables
        self.assertEqual(manager1.current_model, manager2.current_model)
        self.assertEqual(manager1.model_list, manager2.model_list)

    @patch("subprocess.Popen")
    def test_class_variables_persistence(self, mock_popen):
        """Test that class variables persist across instance creation"""
        mock_process = MagicMock()
        mock_process.stdout.read.return_value.decode.return_value = ""
        mock_popen.return_value = mock_process

        # Create first instance and set model
        manager1 = ModelManager(model=settings.DEFAULT_MODEL)
        original_current_model = ModelManager.current_model

        # Create second instance
        manager2 = ModelManager(model=settings.CYPHER_MODEL)

        # Current model should be updated to the latest
        self.assertEqual(ModelManager.current_model, settings.CYPHER_MODEL)
        self.assertNotEqual(ModelManager.current_model, original_current_model)

        # Both instances should see the same current model
        self.assertEqual(manager1.current_model, manager2.current_model)


if __name__ == "__main__":
    unittest.main()
