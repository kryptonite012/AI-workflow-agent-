#!/usr/bin/env python3
"""
Test script to verify shell command fixes and error routing.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Initialize Rich Traceback Manager
from src.ui.diagnostics.rich_traceback_manager import RichTracebackManager

RichTracebackManager.initialize(
    show_locals=False,
    max_frames=10,
    suppress_modules=[
        "click",
        "rich",
        "__main__",
        "runpy",
        "threading",
        "socket",
        "pickle",
    ],
)

# Import required modules
from src.config import settings
from src.utils.socket_manager import SocketManager
from src.tools.lggraph_tools.tools.run_shell_command_tool import run_shell_command


def test_shell_command_fixes():
    """Test the shell command fixes"""

    print("🧪 Testing Shell Command Fixes")
    print("=" * 50)

    # Initialize socket connection
    socket_manager = SocketManager()
    socket_con = socket_manager.get_socket_connection()

    if socket_con and socket_con._is_connected():
        print("✅ Debug console connected")
        settings.socket_con = socket_con
    else:
        print("❌ Debug console not connected - start socket system_logging first")
        print("   Run: python src/utils/error_transfer.py")
        return

    print("\n🎯 Testing shell command scenarios...")

    # Test 1: Simple command that works
    print("\n1. Testing simple command (should work):")
    try:
        result = run_shell_command("echo Hello World")
        print(f"   Result: {result}")
    except Exception as e:
        RichTracebackManager.handle_exception(e, context="Test 1: Simple Command")

    # Test 2: Command with Unicode output (potential encoding issue)
    print("\n2. Testing command with potential Unicode issues:")
    try:
        result = run_shell_command("dir /w")  # Windows dir command
        print(f"   Result length: {len(result)} characters")
        print(f"   First 100 chars: {result[:100]}...")
    except Exception as e:
        RichTracebackManager.handle_exception(e, context="Test 2: Unicode Command")

    # Test 3: Command that fails
    print("\n3. Testing command that fails:")
    try:
        result = run_shell_command("nonexistent_command_12345")
        print(f"   Result: {result}")
    except Exception as e:
        RichTracebackManager.handle_exception(e, context="Test 3: Failed Command")

    # Test 4: Command with no output
    print("\n4. Testing command with no output:")
    try:
        result = run_shell_command("echo. > nul")  # Windows command with no output
        print(f"   Result: '{result}'")
    except Exception as e:
        RichTracebackManager.handle_exception(e, context="Test 4: No Output Command")

    # Test 5: Test the wrapper class
    print("\n5. Testing ShellCommandWrapper:")
    try:
        from src.tools.lggraph_tools.wrappers.run_shell_comand_wrapper import (
            ShellCommandWrapper,
        )
        from src.tools.lggraph_tools.tool_response_manager import ToolResponseManager

        # Initialize ToolResponseManager
        tool_manager = ToolResponseManager()

        # Test wrapper
        wrapper = ShellCommandWrapper("echo Testing Wrapper", capture_output=True)

        # Get response
        responses = tool_manager.get_response()
        if responses:
            print(f"   Wrapper result: {responses[-1].content}")
        else:
            print("   No response from wrapper")

    except Exception as e:
        RichTracebackManager.handle_exception(e, context="Test 5: Wrapper Test")

    print("\n✅ Shell command tests completed!")
    print("📋 Check debug window for any error panels")
    print("📋 Main window should remain clean")

    # Cleanup
    socket_manager.close_connection()


if __name__ == "__main__":
    test_shell_command_fixes()
