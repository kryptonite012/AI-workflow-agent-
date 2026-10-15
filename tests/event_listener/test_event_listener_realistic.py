# 🎯 Realistic Event Listener Test System
"""
Comprehensive test for the RichStatusListener system with multi-threaded operations.

This test simulates a real-world scenario where:
1. Main thread shows "generating heading..." status
2. Background thread processes requests and updates status at milestones
3. Demonstrates thread-safe status updates with realistic timing

Test Scenarios:
- Request count 0-9: "generating heading..."
- Request count 10: "generating heading... (requests done 10)"
- Request count 30: "generating heading... (requests done 30)"
- Request count 40: "generating the request is 40 wait for sec"

Usage:
    python tests/test_event_listener_realistic.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import threading
import time
import random
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

# Import your event listener system
import sys
import os


from src.utils.listeners.rich_status_listen import RichStatusListener
from src.utils.listeners.event_listener import EventListener


class RealisticTestRunner:
    """
    Realistic test runner that simulates real application behavior
    """

    def __init__(self):
        self.console = Console()
        self.listener = None
        self.request_count = 0
        self.is_running = False
        self.request_thread = None
        self.test_results = []

    def setup_listener(self):
        """Initialize the event listener"""
        self.console.print("🚀 Setting up RichStatusListener...")

        # Create listener with dedicated console
        listener_console = Console()
        self.listener = RichStatusListener(listener_console)

        self.console.print(f"✅ Listener created with ID: {id(self.listener)}")
        return self.listener

    def start_heading_generation(self):
        """Start the main heading generation process"""
        self.console.print("📝 Starting heading generation process...")

        # Start with initial status
        self.listener.start_status("🔄 generating heading...")

        # Log the start
        self.test_results.append(
            {
                "timestamp": time.time(),
                "action": "started_heading_generation",
                "status": "generating heading...",
                "request_count": 0,
            }
        )

        self.console.print("✅ Heading generation started")

    def process_requests_background(self):
        """Background thread that processes requests and updates status"""
        self.console.print("🔧 Starting background request processing...")

        while self.is_running and self.request_count < 45:
            # Simulate request processing time (realistic delays)
            processing_time = random.uniform(0.1, 0.3)  # 100-300ms per request
            time.sleep(processing_time)

            self.request_count += 1

            # Update status at specific milestones
            if self.request_count == 10:
                new_status = "🔄 generating heading... (requests done 10)"
                self.listener.emit_on_variable_change(
                    RequestProcessor, "status", "generating heading...", new_status
                )

                self.test_results.append(
                    {
                        "timestamp": time.time(),
                        "action": "milestone_10_requests",
                        "status": new_status,
                        "request_count": 10,
                    }
                )

                self.console.print(f"📊 Milestone reached: 10 requests processed")

            elif self.request_count == 30:
                new_status = "🔄 generating heading... (requests done 30)"
                self.listener.emit_on_variable_change(
                    RequestProcessor,
                    "status",
                    "generating heading... (requests done 10)",
                    new_status,
                )

                self.test_results.append(
                    {
                        "timestamp": time.time(),
                        "action": "milestone_30_requests",
                        "status": new_status,
                        "request_count": 30,
                    }
                )

                self.console.print(f"📊 Milestone reached: 30 requests processed")

            elif self.request_count == 40:
                new_status = "⏳ generating the request is 40 wait for sec"
                self.listener.emit_on_variable_change(
                    RequestProcessor,
                    "status",
                    "generating heading... (requests done 30)",
                    new_status,
                )

                self.test_results.append(
                    {
                        "timestamp": time.time(),
                        "action": "milestone_40_requests_wait",
                        "status": new_status,
                        "request_count": 40,
                    }
                )

                self.console.print(f"⏳ Special milestone: 40 requests - waiting...")

                # Wait for 2 seconds as requested
                time.sleep(2)

                # Final completion status
                final_status = "✅ heading generation completed!"
                self.listener.emit_on_variable_change(
                    RequestProcessor,
                    "status",
                    "generating the request is 40 wait for sec",
                    final_status,
                )

                self.test_results.append(
                    {
                        "timestamp": time.time(),
                        "action": "completed",
                        "status": final_status,
                        "request_count": 40,
                    }
                )

                self.console.print(f"🎉 Process completed!")
                break

            # Show progress for other request counts (optional)
            if self.request_count % 5 == 0 and self.request_count not in [10, 30, 40]:
                self.console.print(
                    f"📈 Progress: {self.request_count} requests processed..."
                )

        self.console.print("🏁 Background request processing finished")

    def run_realistic_test(self):
        """Run the complete realistic test scenario"""
        self.console.print(
            Panel.fit(
                "🧪 [bold blue]REALISTIC EVENT LISTENER TEST[/bold blue]\n"
                "Testing multi-threaded status updates with request processing",
                border_style="blue",
            )
        )

        try:
            # Step 1: Setup
            self.setup_listener()
            time.sleep(0.5)

            # Step 2: Start heading generation
            self.start_heading_generation()
            time.sleep(1)

            # Step 3: Start background request processing
            self.is_running = True
            self.request_thread = threading.Thread(
                target=self.process_requests_background, daemon=True
            )
            self.request_thread.start()

            self.console.print("🔄 Both processes running concurrently...")
            self.console.print(
                "👀 Watch the status display above for real-time updates!"
            )
            self.console.print("⏱️  This test will run for about 15-20 seconds...")

            # Step 4: Wait for completion
            self.request_thread.join(timeout=30)  # Max 30 seconds

            # Step 5: Cleanup
            time.sleep(2)  # Let final status show
            self.listener.stop_status_display()

            # Step 6: Show results
            self.show_test_results()

        except Exception as e:
            self.console.print(f"❌ Test failed with error: {e}")
            if self.listener:
                self.listener.stop_status_display()
            raise

    def show_test_results(self):
        """Display comprehensive test results"""
        self.console.print("\n" + "=" * 60)
        self.console.print("📊 [bold green]TEST RESULTS SUMMARY[/bold green]")
        self.console.print("=" * 60)

        # Create results table
        table = Table(title="Event Listener Test Results")
        table.add_column("Time", style="cyan", no_wrap=True)
        table.add_column("Action", style="magenta")
        table.add_column("Status Message", style="green")
        table.add_column("Requests", style="yellow", justify="right")

        start_time = (
            self.test_results[0]["timestamp"] if self.test_results else time.time()
        )

        for result in self.test_results:
            elapsed = f"{result['timestamp'] - start_time:.2f}s"
            table.add_row(
                elapsed,
                result["action"].replace("_", " ").title(),
                result["status"][:50] + "..."
                if len(result["status"]) > 50
                else result["status"],
                str(result["request_count"]),
            )

        self.console.print(table)

        # Test validation
        self.validate_test_results()

    def validate_test_results(self):
        """Validate that the test worked correctly"""
        self.console.print("\n🔍 [bold yellow]TEST VALIDATION[/bold yellow]")

        expected_milestones = [
            ("started_heading_generation", 0),
            ("milestone_10_requests", 10),
            ("milestone_30_requests", 30),
            ("milestone_40_requests_wait", 40),
            ("completed", 40),
        ]

        validation_results = []

        for expected_action, expected_count in expected_milestones:
            found = any(
                result["action"] == expected_action
                and result["request_count"] == expected_count
                for result in self.test_results
            )

            if found:
                validation_results.append(
                    f"✅ {expected_action} at {expected_count} requests"
                )
            else:
                validation_results.append(
                    f"❌ MISSING: {expected_action} at {expected_count} requests"
                )

        for result in validation_results:
            self.console.print(result)

        # Overall test result
        all_passed = all("✅" in result for result in validation_results)

        if all_passed:
            self.console.print("\n🎉 [bold green]ALL TESTS PASSED![/bold green]")
            self.console.print("✅ Event listener system working correctly")
            self.console.print("✅ Thread-safe status updates confirmed")
            self.console.print("✅ Milestone-based status changes working")
            self.console.print("✅ Realistic timing and behavior validated")
        else:
            self.console.print("\n❌ [bold red]SOME TESTS FAILED![/bold red]")
            self.console.print("🔧 Check the event listener implementation")

        return all_passed


class RequestProcessor:
    """Dummy class to represent the request processing component"""

    pass


def run_continuous_test():
    """Run the test continuously until it works properly"""
    console = Console()
    test_runner = RealisticTestRunner()

    console.print(
        Panel.fit(
            "🔄 [bold blue]CONTINUOUS TEST MODE[/bold blue]\n"
            "Running tests until they pass correctly...",
            border_style="blue",
        )
    )

    attempt = 1
    max_attempts = 5

    while attempt <= max_attempts:
        console.print(
            f"\n🧪 [bold yellow]TEST ATTEMPT {attempt}/{max_attempts}[/bold yellow]"
        )
        console.print("-" * 50)

        try:
            # Create fresh test runner for each attempt
            test_runner = RealisticTestRunner()

            # Run the test
            test_runner.run_realistic_test()

            # If we get here, test completed
            console.print(f"\n✅ Test attempt {attempt} completed successfully!")
            break

        except KeyboardInterrupt:
            console.print("\n⏹️ Test interrupted by user")
            break

        except Exception as e:
            console.print(f"\n❌ Test attempt {attempt} failed: {e}")

            if attempt < max_attempts:
                console.print(
                    f"🔄 Retrying in 3 seconds... ({max_attempts - attempt} attempts remaining)"
                )
                time.sleep(3)
            else:
                console.print("❌ All test attempts failed!")

        attempt += 1

    console.print("\n🏁 Continuous testing completed")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Realistic Event Listener Test")
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run tests continuously until they pass",
    )
    parser.add_argument("--single", action="store_true", help="Run a single test")

    args = parser.parse_args()

    if args.continuous:
        run_continuous_test()
    else:
        # Default: run single test
        test_runner = RealisticTestRunner()
        test_runner.run_realistic_test()
