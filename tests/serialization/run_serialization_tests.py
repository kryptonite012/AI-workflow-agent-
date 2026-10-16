#!/usr/bin/env python3
"""
Serialization Test Runner

This script runs all serialization tests and provides a comprehensive
comparison of different serialization methods for Rich objects.
"""

import sys
import os
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Rich imports for output formatting
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich.align import Align
from rich.box import DOUBLE

# Import test modules
from test_rich_serialization import RichSerializationTester
from test_socket_transmission import SocketTransmissionTester


class SerializationTestSuite:
    """Complete serialization test suite runner"""

    def __init__(self):
        self.console = Console(width=120, force_terminal=True)
        self.results = {}

    def print_header(self):
        """Print test suite header"""
        header_text = Text(
            "🧪 RICH OBJECT SERIALIZATION TEST SUITE", style="bold magenta"
        )
        header_panel = Panel(
            Align.center(header_text),
            box=DOUBLE,
            border_style="magenta",
            padding=(1, 2),
        )

        self.console.print(
            Rule("🚀 STARTING COMPREHENSIVE SERIALIZATION TESTS", style="magenta")
        )
        self.console.print(header_panel)
        self.console.print(Rule(style="magenta"))

        # Test overview
        overview_table = Table(title="📋 Test Overview", box=DOUBLE)
        overview_table.add_column("Test Category", style="cyan")
        overview_table.add_column("Description", style="white")
        overview_table.add_column("Purpose", style="green")

        overview_table.add_row(
            "🎨 Rich Serialization",
            "Test different serialization methods",
            "Compare pickle, dill, string conversion, JSON",
        )
        overview_table.add_row(
            "📡 Socket Transmission",
            "Test actual socket transmission",
            "Simulate real-world error routing scenario",
        )

        self.console.print(overview_table)
        self.console.print()

    def run_rich_serialization_tests(self):
        """Run Rich object serialization tests"""
        print("\n" + "=" * 120)
        print("🎨 PHASE 1: RICH OBJECT SERIALIZATION TESTS")
        print("=" * 120)

        tester = RichSerializationTester()
        results = tester.run_all_tests()

        self.results["serialization"] = results

        # Summary
        successful = sum(1 for r in results if r["success"])
        total = len(results)

        print(f"\n📊 Phase 1 Results: {successful}/{total} methods successful")

        return results

    def run_socket_transmission_tests(self):
        """Run socket transmission tests"""
        print("\n" + "=" * 120)
        print("📡 PHASE 2: SOCKET TRANSMISSION TESTS")
        print("=" * 120)

        tester = SocketTransmissionTester()
        tester.run_transmission_tests()

        print(f"\n📊 Phase 2 Results: Socket transmission tests completed")

    def generate_final_report(self):
        """Generate final comprehensive report"""
        print("\n" + "=" * 120)
        print("📊 FINAL COMPREHENSIVE REPORT")
        print("=" * 120)

        # Create comprehensive comparison table
        if "serialization" in self.results:
            comparison_table = Table(
                title="🔍 Serialization Methods - Detailed Comparison", box=DOUBLE
            )
            comparison_table.add_column("Method", style="cyan", no_wrap=True)
            comparison_table.add_column("Success", style="magenta")
            comparison_table.add_column("Size", justify="right", style="green")
            comparison_table.add_column("Speed", style="yellow")
            comparison_table.add_column("Reconstruction", style="blue")
            comparison_table.add_column("Use Case", style="white")

            for result in self.results["serialization"]:
                method = result["method"]
                success = "✅" if result["success"] else "❌"
                size = str(result["serialized_size"]) if result["success"] else "N/A"

                # Determine speed (based on typical performance)
                if method == "pickle":
                    speed = "🚀 Fast"
                elif method == "dill":
                    speed = "🐌 Slow"
                elif method == "rich_to_string":
                    speed = "⚡ Very Fast"
                elif method == "json_custom":
                    speed = "🚀 Fast"
                else:
                    speed = "❓ Unknown"

                # Reconstruction capability
                if method in ["pickle", "dill"] and result["success"]:
                    reconstruction = "✅ Full Object"
                elif method in ["rich_to_string", "json_custom"] and result["success"]:
                    reconstruction = "⚠️ Visual Only"
                else:
                    reconstruction = "❌ None"

                # Best use case
                if method == "pickle":
                    use_case = "Simple objects, same Python version"
                elif method == "dill":
                    use_case = "Complex objects, robust serialization"
                elif method == "rich_to_string":
                    use_case = "Socket transmission, visual display"
                elif method == "json_custom":
                    use_case = "Cross-platform, metadata preservation"
                else:
                    use_case = "Unknown"

                comparison_table.add_row(
                    method.replace("_", " ").title(),
                    success,
                    size,
                    speed,
                    reconstruction,
                    use_case,
                )

            self.console.print(comparison_table)

        # Recommendations
        self.print_recommendations()

    def print_recommendations(self):
        """Print final recommendations"""
        print("\n💡 FINAL RECOMMENDATIONS:")
        print("=" * 120)

        recommendations = [
            {
                "scenario": "🚨 Error Routing (Your Use Case)",
                "method": "Rich-to-String Conversion",
                "reason": "Preserves visual formatting, works across processes, no reconstruction needed",
            },
            {
                "scenario": "💾 Object Persistence",
                "method": "Dill Serialization",
                "reason": "Most robust for complex objects, handles Rich objects better than pickle",
            },
            {
                "scenario": "🌐 Cross-Platform Communication",
                "method": "JSON with Custom Encoding",
                "reason": "Platform independent, includes metadata, structured format",
            },
            {
                "scenario": "⚡ High Performance",
                "method": "Pickle (if compatible)",
                "reason": "Fastest serialization/deserialization for compatible objects",
            },
        ]

        rec_table = Table(title="🎯 Scenario-Based Recommendations", box=DOUBLE)
        rec_table.add_column("Scenario", style="cyan")
        rec_table.add_column("Recommended Method", style="green")
        rec_table.add_column("Reason", style="white")

        for rec in recommendations:
            rec_table.add_row(rec["scenario"], rec["method"], rec["reason"])

        self.console.print(rec_table)

        # Specific implementation guidance
        print("\n🔧 IMPLEMENTATION GUIDANCE FOR YOUR ERROR ROUTING:")
        print("=" * 80)

        implementation_code = """
# In SocketCon.send_error() method:
def send_error(self, error_message, close_socket: bool = False):
    try:
        # Handle Rich objects by converting to string representation
        if hasattr(error_message, '__rich_console__'):
            from rich.console import Console
            import io
            temp_console = Console(file=io.StringIO(), width=120, force_terminal=True)
            temp_console.print(error_message)
            message_str = temp_console.file.getvalue()
        else:
            message_str = str(error_message)
        
        self.client_socket.sendall(message_str.encode('utf-8'))
    except Exception as e:
        # Handle errors...
"""

        from rich.syntax import Syntax

        syntax = Syntax(
            implementation_code, "python", theme="monokai", line_numbers=True
        )

        implementation_panel = Panel(
            syntax,
            title="🔧 Recommended Implementation",
            border_style="green",
            padding=(1, 1),
        )

        self.console.print(implementation_panel)

    def run_complete_test_suite(self):
        """Run the complete test suite"""
        start_time = time.time()

        # Print header
        self.print_header()

        try:
            # Phase 1: Serialization tests
            self.run_rich_serialization_tests()

            # Phase 2: Socket transmission tests
            self.run_socket_transmission_tests()

            # Generate final report
            self.generate_final_report()

        except KeyboardInterrupt:
            print("\n⚠️ Tests interrupted by user")
        except Exception as e:
            print(f"\n❌ Test suite error: {e}")

        # Final summary
        end_time = time.time()
        duration = end_time - start_time

        print(f"\n🎉 TEST SUITE COMPLETED!")
        print(f"⏱️ Total duration: {duration:.2f} seconds")
        print("=" * 120)


def main():
    """Main function"""
    print("🧪 Starting Rich Object Serialization Test Suite...")

    # Check dependencies
    try:
        import dill

        print("✅ Dill available for enhanced serialization tests")
    except ImportError:
        print("⚠️ Dill not available - install with: pip install dill")

    # Run test suite
    suite = SerializationTestSuite()
    suite.run_complete_test_suite()


if __name__ == "__main__":
    main()
