#!/usr/bin/env python3
"""
Demonstration of automatic subprocess log server management
This shows how lggraph.py will now work with automatic log server startup
"""

import time

from rich.panel import Panel
from rich.text import Text

# Add project imports
from utils.socket_manager import socket_manager

from src.config import settings


def demo_automatic_logging():
    """Demonstrate automatic log server startup and usage"""
    console = settings.console

    console.print(
        Panel.fit(
            Text("🚀 Automatic Log Server Demo", style="bold magenta"),
            title="LangGraph Chatbot - Subprocess Logging",
            style="bold blue",
        )
    )

    console.print("\n📋 This demo shows how your lggraph.py will now work:")
    console.print("   1. ✅ Automatically starts log server when needed")
    console.print("   2. ✅ No need to manually run utils/error_transfer.py")
    console.print("   3. ✅ Handles all system_logging seamlessly")
    console.print("   4. ✅ Cleans up when application exits")

    console.print("\n🔄 Starting demonstration...")
    time.sleep(2)

    # Step 1: Get socket connection (this will auto-start log server)
    console.print("\n1. 📡 Getting socket connection (will auto-start log server)...")
    socket_con = socket_manager.get_socket_connection()

    if socket_con:
        console.print("   ✅ Socket connection established!")

        if socket_manager.is_log_server_running():
            pid = socket_manager._log_server_process.pid
            console.print(f"   ✅ Log server subprocess running (PID: {pid})")

        # Step 2: Send some demo log messages
        console.print("\n2. 📤 Sending demo log messages...")

        demo_messages = [
            "🚀 Application started successfully",
            "📊 Loading configuration...",
            "🤖 Initializing LLM models...",
            "🔗 Setting up LangGraph workflow...",
            "⚠️ Warning: Large document detected, this may take time",
            "🔍 Performing RAG search...",
            "💾 Saving results to knowledge graph...",
            "✅ Operation completed successfully",
        ]

        for i, message in enumerate(demo_messages, 1):
            console.print(
                f"   Sending message {i}/{len(demo_messages)}: {message[:40]}..."
            )
            socket_manager.send_error(f"[DEMO {i:02d}] {message}")
            time.sleep(1)  # Realistic delay between operations

        console.print("   ✅ All demo messages sent!")

        # Step 3: Show subprocess status
        console.print("\n3. 📊 Checking subprocess status...")
        if socket_manager.is_log_server_running():
            console.print("   ✅ Log server subprocess is healthy")
        else:
            console.print("   ❌ Log server subprocess not detected")

        # Step 4: Demonstrate error handling
        console.print("\n4. 🧪 Testing error scenarios...")
        error_scenarios = [
            "ConnectionError: Failed to connect to Neo4j database",
            "TimeoutError: RAG search timed out after 30 seconds",
            "ValueError: Invalid JSON format in API response",
            "FileNotFoundError: Configuration file not found",
        ]

        for i, error in enumerate(error_scenarios, 1):
            console.print(f"   Simulating error {i}: {error[:50]}...")
            socket_manager.send_error(f"[ERROR {i:02d}] {error}")
            time.sleep(0.5)

        console.print("   ✅ Error handling demonstration complete")

        # Step 5: Show what happens during normal operation
        console.print("\n5. 🔄 Simulating normal application workflow...")

        workflow_steps = [
            ("User Input", "User asked: 'What is machine learning?'"),
            ("Classification", "Message classified as: tool"),
            ("Tool Selection", "Selected tool: google_search"),
            ("Web Search", "Searching for: machine learning basics"),
            ("Response Generation", "Generating response from search results"),
            ("User Output", "Response delivered to user successfully"),
        ]

        for step_name, step_message in workflow_steps:
            console.print(f"   {step_name}: {step_message}")
            socket_manager.send_error(f"[WORKFLOW] {step_name}: {step_message}")
            time.sleep(0.8)

        console.print("   ✅ Workflow simulation complete")

    else:
        console.print("   ❌ Failed to establish socket connection")
        console.print(
            "   This might happen if there are permission issues or port conflicts"
        )
        return False

    return True


def demo_cleanup():
    """Demonstrate proper cleanup"""
    console = settings.console
    console.print("\n6. 🧹 Demonstrating cleanup process...")

    console.print("   📝 In your actual lggraph.py, this happens when:")
    console.print("      - User types 'exit'")
    console.print("      - Application is interrupted (Ctrl+C)")
    console.print("      - Application encounters fatal error")

    console.print("   🛑 Closing socket connection and stopping subprocess...")
    socket_manager.close_connection()

    time.sleep(2)

    if not socket_manager.is_log_server_running():
        console.print("   ✅ Log server subprocess stopped cleanly")
    else:
        console.print(
            "   ⚠️ Log server subprocess still running (may need manual cleanup)"
        )

    console.print("   ✅ Cleanup demonstration complete")


def show_integration_example():
    """Show how this integrates with lggraph.py"""
    console = settings.console
    console.print("\n" + "=" * 80)
    console.print("📖 HOW THIS INTEGRATES WITH YOUR LGGRAPH.PY")
    console.print("=" * 80)

    console.print("\n🔧 Your lggraph.py now works like this:")

    code_example = """
# In lggraph.py - this is what happens now:

from utils.socket_manager import socket_manager

# When you run lggraph.py:
socket_con = socket_manager.get_socket_connection()
# ↑ This automatically:
#   1. Checks if log server is running
#   2. If not, starts it as subprocess  
#   3. Connects to it
#   4. Returns working connection

# Throughout your application:
if socket_con:
    socket_con.send_error("Your log message")
else:
    print("Your log message")  # Fallback

# When application exits:
socket_manager.close_connection()
# ↑ This automatically:
#   1. Closes socket connection
#   2. Stops the subprocess
#   3. Cleans up resources
"""

    console.print(Panel(code_example, title="Integration Code", style="green"))

    console.print("\n✅ Benefits of this approach:")
    console.print("   🚀 Fully automatic - no manual server startup needed")
    console.print("   🔄 Self-managing - handles crashes and restarts")
    console.print("   🧹 Clean - proper resource cleanup")
    console.print("   🛡️ Robust - graceful fallback if system_logging fails")
    console.print("   👥 User-friendly - works out of the box")


def main():
    """Main demonstration function"""
    console = settings.console
    try:
        console.print("🎬 Starting Automatic Subprocess Logging Demo...")
        console.print("   (This simulates what happens when you run lggraph.py)")

        time.sleep(2)

        # Run the main demo
        if demo_automatic_logging():
            demo_cleanup()
            show_integration_example()

            console.print("\n🎉 DEMONSTRATION COMPLETE!")
            console.print("\n📋 What this means for you:")
            console.print("   ✅ Your lggraph.py is now fully self-contained")
            console.print("   ✅ No need to manually start log servers")
            console.print("   ✅ Logging 'just works' automatically")
            console.print("   ✅ Clean shutdown when application exits")

        else:
            console.print("\n❌ Demo failed - check error messages above")

    except KeyboardInterrupt:
        console.print("\n\n⏹️ Demo interrupted by user")
        console.print("🧹 Cleaning up...")
        try:
            socket_manager.close_connection()
        except:
            pass
        console.print("✅ Cleanup complete")

    except Exception as e:
        console.print(f"\n❌ Demo crashed: {e}")
        console.print("🧹 Attempting cleanup...")
        try:
            socket_manager.close_connection()
        except:
            pass


if __name__ == "__main__":
    main()
