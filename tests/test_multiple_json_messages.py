#!/usr/bin/env python3
"""
Test script to verify multiple JSON message handling in RichErrorPrint
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import sys
from pathlib import Path

# Add project root to Python path

from src.ui.rich_error_print import RichErrorPrint
from rich.console import Console


def test_multiple_json_messages():
    """Test the multiple JSON message parsing"""

    # Create RichErrorPrint instance
    console = Console()
    rich_print = RichErrorPrint(console)

    # Test data - multiple concatenated JSON messages (like your actual output)
    test_message = """{"obj_type": "str", "data_type": "DebugMessage", "timestamp": "2025-08-14T16:06:39.413585", "data": {"heading": "OPENAI • CONTENT_FOUND", "body": "Content found: test content", "level": "INFO", "metadata": {"content_type": "main_content", "content_length": 1207}}}{"obj_type": "str", "data_type": "DebugMessage", "timestamp": "2025-08-14T16:06:39.413654", "data": {"heading": "OPENAI • REASONING_FOUND", "body": "Reasoning content found: test reasoning", "level": "INFO", "metadata": {"content_type": "reasoning_content", "content_length": 5308}}}{"obj_type": "str", "data_type": "ToolResponse", "timestamp": "2025-08-14T16:06:39.413787", "data": {"tool_name": "RunShellCommand", "status": "failed", "response_summary": "Test tool response", "execution_time": 0.0, "metadata": {"evaluation_status": "failed", "context": "tool_evaluation"}}}"""

    print("🧪 Testing multiple JSON message parsing...")
    print("=" * 80)

    # Process the test message
    rich_print.print_rich(test_message)

    print("=" * 80)
    print("✅ Test completed!")


if __name__ == "__main__":
    test_multiple_json_messages()
