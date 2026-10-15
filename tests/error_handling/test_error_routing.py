#!/usr/bin/env python3
"""
Test script to verify Rich Traceback error routing to debug console.
This should show errors in the debug window, not the user window.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Initialize Rich Traceback Manager (main process style)
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

# Import settings and socket manager
from src.config import settings
from src.utils.socket_manager import SocketManager


def test_error_routing():
    """Test that errors route to debug console properly"""

    print("🧪 Testing Rich Traceback Error Routing")
    print("=" * 50)

    # Initialize socket connection
    socket_manager = SocketManager()
    socket_con = socket_manager.get_socket_connection()

    if socket_con and socket_con._is_connected():
        print("✅ Debug console connected - errors will route to debug window")
        settings.socket_con = socket_con
    else:
        print("❌ Debug console not connected - start socket system_logging first")
        print("   Run: python src/utils/error_transfer.py")
        return

    print("\n🎯 Testing different error types...")
    print("   (Check debug window for Rich Traceback displays)")

    # Test 1: Simple ValueError
    try:
        raise ValueError(
            "Test error for debug routing - this should appear in debug window"
        )
    except Exception as e:
        RichTracebackManager.handle_exception(e, context="Test 1: Simple ValueError")

    # Test 2: Complex error with context
    try:

        def nested_function():
            def deeper_function():
                raise RuntimeError("Deep nested error with complex context")

            deeper_function()

        nested_function()
    except Exception as e:
        RichTracebackManager.handle_exception(
            e,
            context="Test 2: Nested Function Error",
            extra_context={
                "test_type": "nested_function_error",
                "expected_behavior": "should_appear_in_debug_window",
                "user_window": "should_remain_clean",
            },
        )

    # Test 3: Agent mode style error
    try:
        agent_response = "not a list"  # This should be a list
        if not isinstance(agent_response, list):
            raise ValueError(
                "Agent response must be a list of tool execution instructions"
            )
    except Exception as e:
        RichTracebackManager.handle_exception(
            e,
            context="Test 3: Agent Mode Error (typical scenario)",
            extra_context={
                "agent_response_type": type(agent_response).__name__,
                "expected_type": "list",
                "actual_value": str(agent_response)[:50],
            },
        )

    print("\n✅ Error routing tests completed!")
    print("📋 Check debug window for Rich Traceback panels")
    print("📋 User window should remain clean (no tracebacks here)")

    # Cleanup
    socket_manager.close_connection()


if __name__ == "__main__":
    test_error_routing()
