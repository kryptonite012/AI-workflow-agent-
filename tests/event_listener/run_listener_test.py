# 🚀 Simple Test Runner for Event Listener System
"""
Quick and easy way to test the RichStatusListener system.

This script provides multiple test modes:
1. Basic test - Simple functionality check
2. Realistic test - Multi-threaded request processing simulation
3. Continuous test - Runs until working properly

Usage:
    python tests/run_listener_test.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import sys
import os
import time
import threading
from rich.console import Console
from rich.panel import Panel

# Add project root to path

from src.utils.listeners.rich_status_listen import RichStatusListener


def basic_test():
    """Basic functionality test"""
    console = Console()
    console.print("🧪 [bold blue]BASIC EVENT LISTENER TEST[/bold blue]")

    # Create listener
    listener = RichStatusListener(Console())
    listener.start_status("🚀 Basic test starting...")

    # Test simple updates
    time.sleep(1)
    listener.emit_on_variable_change(TestClass, "status", "idle", "📄 Processing...")

    time.sleep(2)
    listener.emit_on_variable_change(TestClass, "status", "processing", "✅ Complete!")

    time.sleep(2)
    listener.stop_status_display()

    console.print("✅ Basic test completed!")


def realistic_threading_test():
    """Realistic multi-threaded test as requested"""
    console = Console()
    console.print("🧪 [bold blue]REALISTIC THREADING TEST[/bold blue]")
    console.print(
        "📝 Simulating heading generation with background request processing..."
    )

    # Create listener
    listener = RichStatusListener(Console())
    listener.start_status("🔄 generating heading...")

    # Shared state
    request_count = 0
    is_running = True

    def process_requests():
        nonlocal request_count, is_running

        while is_running and request_count < 45:
            time.sleep(0.2)  # Simulate request processing
            request_count += 1

            # Update at milestones
            if request_count == 10:
                listener.emit_on_variable_change(
                    TestClass,
                    "status",
                    "generating heading...",
                    "🔄 generating heading... (requests done 10)",
                )
                console.print("📊 Milestone: 10 requests processed")

            elif request_count == 30:
                listener.emit_on_variable_change(
                    TestClass,
                    "status",
                    "generating heading... (requests done 10)",
                    "🔄 generating heading... (requests done 30)",
                )
                console.print("📊 Milestone: 30 requests processed")

            elif request_count == 40:
                listener.emit_on_variable_change(
                    TestClass,
                    "status",
                    "generating heading... (requests done 30)",
                    "⏳ generating the request is 40 wait for sec",
                )
                console.print("⏳ Special milestone: 40 requests - waiting...")

                # Wait as requested
                time.sleep(2)

                # Final status
                listener.emit_on_variable_change(
                    TestClass,
                    "status",
                    "generating the request is 40 wait for sec",
                    "✅ heading generation completed!",
                )
                console.print("🎉 Process completed!")
                break

    # Start background thread
    request_thread = threading.Thread(target=process_requests, daemon=True)
    request_thread.start()

    console.print("🔄 Background request processing started...")
    console.print("👀 Watch the status display for real-time updates!")

    # Wait for completion
    request_thread.join(timeout=20)

    time.sleep(2)
    listener.stop_status_display()

    console.print(f"✅ Realistic test completed! Processed {request_count} requests")


def continuous_test():
    """Run tests continuously until they work"""
    console = Console()
    console.print("🔄 [bold blue]CONTINUOUS TEST MODE[/bold blue]")

    attempt = 1
    while attempt <= 3:
        console.print(f"\n🧪 Test Attempt {attempt}")
        console.print("-" * 30)

        try:
            realistic_threading_test()
            console.print(f"✅ Attempt {attempt} successful!")
            break
        except Exception as e:
            console.print(f"❌ Attempt {attempt} failed: {e}")
            if attempt < 3:
                console.print("🔄 Retrying in 2 seconds...")
                time.sleep(2)

        attempt += 1

    console.print("🏁 Continuous testing completed")


class TestClass:
    """Dummy class for testing"""

    pass


def main():
    """Main test runner with menu"""
    console = Console()

    console.print(
        Panel.fit(
            "🧪 [bold blue]EVENT LISTENER TEST SUITE[/bold blue]\n\n"
            "Choose a test mode:\n"
            "1. Basic Test - Simple functionality\n"
            "2. Realistic Test - Multi-threaded simulation\n"
            "3. Continuous Test - Run until working\n"
            "4. All Tests - Run everything",
            border_style="blue",
        )
    )

    try:
        choice = input("\nEnter your choice (1-4): ").strip()

        if choice == "1":
            basic_test()
        elif choice == "2":
            realistic_threading_test()
        elif choice == "3":
            continuous_test()
        elif choice == "4":
            console.print("🚀 Running all tests...")
            basic_test()
            time.sleep(2)
            realistic_threading_test()
            time.sleep(2)
            continuous_test()
        else:
            console.print("❌ Invalid choice. Running realistic test by default...")
            realistic_threading_test()

    except KeyboardInterrupt:
        console.print("\n⏹️ Test interrupted by user")
    except Exception as e:
        console.print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    main()
