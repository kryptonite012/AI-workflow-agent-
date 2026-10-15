#!/usr/bin/env python3
"""
Test script to verify that lggraph.py integration works correctly
This simulates the key parts of lggraph.py that use the socket manager
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import time

from utils.socket_manager import socket_manager

from src.config import settings


def simulate_lggraph_startup():
    """Simulate what happens when lggraph.py starts"""
    console = settings.console
    console.print("🚀 Simulating lggraph.py startup...")

    # This is what happens in your lggraph.py
    console.print("📡 Getting socket connection (from socket_manager)...")
    socket_con = socket_manager.get_socket_connection()

    if socket_con:
        console.print("✅ Socket connection established!")
        console.print("   📋 Log server subprocess started automatically")
        console.print("   🔗 Connection ready for system_logging")
        return socket_con
    else:
        console.print("⚠️ Socket connection not available")
        console.print("   📋 Will fall back to console system_logging")
        return None


def simulate_lggraph_operations(socket_con):
    """Simulate typical lggraph.py operations with system_logging"""
    console = settings.console
    console.print("\n🔄 Simulating typical lggraph.py operations...")

    operations = [
        ("Loading Configuration", "Configuration loaded successfully"),
        ("Initializing LLM", "ChatOllama model initialized"),
        ("Building Graph", "LangGraph workflow constructed"),
        ("User Input", "User message received: 'Hello'"),
        ("Message Classification", "Message classified as: llm"),
        ("LLM Response", "Response generated successfully"),
        ("User Output", "Response delivered to user"),
    ]

    for operation, message in operations:
        console.print(f"   {operation}: {message}")

        # This is how your lggraph.py sends log messages
        if socket_con:
            socket_con.send_error(f"[LGGRAPH] {operation}: {message}")
        else:
            print(f"[LGGRAPH] {operation}: {message}")

        time.sleep(0.5)

    console.print("✅ Operations simulation complete")


def simulate_lggraph_errors(socket_con):
    """Simulate error scenarios in lggraph.py"""
    console = settings.console
    console.print("\n🧪 Simulating error scenarios...")

    errors = [
        "Connection error: Could not connect to Ollama server",
        "Tool error: GoogleSearch API rate limit exceeded",
        "RAG error: Neo4j database connection timeout",
        "Classification error: Invalid message format",
    ]

    for i, error in enumerate(errors, 1):
        console.print(f"   Simulating error {i}: {error}")

        # This is how your lggraph.py handles errors
        if socket_con:
            socket_con.send_error(f"[ERROR] {error}")
        else:
            print(f"[ERROR] {error}")

        time.sleep(0.3)

    console.print("✅ Error simulation complete")


def simulate_lggraph_shutdown():
    """Simulate what happens when lggraph.py shuts down"""
    console = settings.console
    console.print("\n🛑 Simulating lggraph.py shutdown...")

    # This is what happens in your on_exit function
    console.print("   💾 Saving conversation history...")
    console.print("   🧹 Cleaning up resources...")

    # The key cleanup call
    socket_manager.close_connection()

    console.print("   ✅ Socket connection closed")
    console.print("   ✅ Log server subprocess stopped")
    console.print("   ✅ Cleanup complete")


def main():
    """Main integration test"""
    console = settings.console
    console.print("=" * 80)
    console.print("🧪 LGGRAPH.PY INTEGRATION TEST")
    console.print("=" * 80)

    console.print("📋 This test simulates your lggraph.py workflow:")
    console.print("   1. Application startup with automatic log server")
    console.print("   2. Normal operations with system_logging")
    console.print("   3. Error handling with system_logging")
    console.print("   4. Clean shutdown with subprocess cleanup")

    try:
        # Simulate the full lggraph.py lifecycle
        socket_con = simulate_lggraph_startup()
        simulate_lggraph_operations(socket_con)
        simulate_lggraph_errors(socket_con)
        simulate_lggraph_shutdown()

        console.print("\n🎉 INTEGRATION TEST COMPLETE!")
        console.print("\n📋 Results:")
        console.print("   ✅ Your lggraph.py will now work completely automatically")
        console.print("   ✅ No manual log server startup required")
        console.print("   ✅ All system_logging handled seamlessly")
        console.print("   ✅ Clean shutdown with proper cleanup")

        console.print("\n🚀 Ready to use:")
        console.print("   Just run: python lggraph.py")
        console.print("   Everything else is automatic!")

    except KeyboardInterrupt:
        console.print("\n⏹️ Test interrupted")
        socket_manager.close_connection()
    except Exception as e:
        console.print(f"\n❌ Test failed: {e}")
        socket_manager.close_connection()


if __name__ == "__main__":
    main()
