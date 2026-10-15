#!/usr/bin/env python3
"""
Rich Object Serialization Tests

This module tests different serialization methods for Rich objects:
1. Pickle serialization
2. Dill serialization
3. Rich-to-string conversion
4. JSON with custom encoding

Tests complex Rich Panel objects with various content types.
"""

import sys
import os
import pickle
import json
import base64
import io
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Rich imports
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.syntax import Syntax
from rich.traceback import Traceback
from rich.progress import Progress, TaskID
from rich.tree import Tree
from rich.columns import Columns
from rich.align import Align
from rich.box import DOUBLE, ROUNDED, HEAVY
from rich.rule import Rule

# Try to import dill for enhanced serialization
try:
    import dill

    DILL_AVAILABLE = True
except ImportError:
    DILL_AVAILABLE = False
    print("⚠️ Dill not available. Install with: pip install dill")


class RichSerializationTester:
    """Test different serialization methods for Rich objects"""

    def __init__(self):
        self.console = Console(width=120, force_terminal=True)
        self.test_results = []

    def create_complex_panel(self) -> Panel:
        """Create a complex Rich Panel with various content types"""

        # Create a complex table
        table = Table(title="🚀 AI-Agent Performance Metrics", box=DOUBLE)
        table.add_column("Component", style="cyan", no_wrap=True)
        table.add_column("Status", style="magenta")
        table.add_column("Response Time", justify="right", style="green")
        table.add_column("Error Rate", justify="right", style="red")

        table.add_row("🤖 Agent Node", "✅ Active", "45ms", "0.2%")
        table.add_row("🔧 Tool Manager", "✅ Active", "23ms", "0.1%")
        table.add_row("🧠 Memory System", "⚠️ Warning", "156ms", "1.2%")
        table.add_row("📡 Socket Connection", "✅ Active", "12ms", "0.0%")

        # Create syntax highlighting
        code_sample = '''
def handle_exception(self, exception: Exception, context: str = "Unknown"):
    """Handle and display exception with rich formatting."""
    error_panel = Panel(
        rich_traceback,
        title=f"🚨 {error_category}: {str(exception)[:100]}",
        subtitle=context_text,
        border_style="red",
        padding=(1, 2)
    )
    return error_panel
'''

        syntax = Syntax(code_sample, "python", theme="monokai", line_numbers=True)

        # Create a tree structure
        tree = Tree("🏗️ Project Architecture")
        tree.add("📁 src/")
        agents_branch = tree.add("🤖 agents/")
        agents_branch.add("agent_mode_node.py")
        agents_branch.add("tool_response_manager.py")

        utils_branch = tree.add("🛠️ utils/")
        utils_branch.add("rich_traceback_manager.py")
        utils_branch.add("socket_manager.py")
        utils_branch.add("error_transfer.py")

        # Create columns layout
        columns_content = Columns(
            [
                Panel("🎯 Status: Production Ready", style="green"),
                Panel("📊 Uptime: 99.9%", style="blue"),
                Panel("⚡ Performance: Optimal", style="yellow"),
            ]
        )

        # Combine everything into a complex panel
        content_parts = [
            Align.center(
                Text("🎨 RICH OBJECT SERIALIZATION TEST", style="bold magenta")
            ),
            Rule("📊 Performance Dashboard", style="blue"),
            table,
            Rule("💻 Code Sample", style="green"),
            syntax,
            Rule("🏗️ Architecture", style="cyan"),
            tree,
            Rule("📈 System Status", style="yellow"),
            columns_content,
            Rule("🔧 Debug Information", style="red"),
            Text("Timestamp: 2025-01-13 14:30:45", style="dim"),
            Text("Process ID: 12345", style="dim"),
            Text("Memory Usage: 245.6 MB", style="dim"),
        ]

        # Join all content
        from rich.console import Group

        content_group = Group(*content_parts)

        # Create the complex panel
        complex_panel = Panel(
            content_group,
            title="🚨 COMPLEX RICH PANEL - SERIALIZATION TEST",
            subtitle="Multi-component Rich object with tables, syntax, trees, and more",
            border_style="bright_red",
            box=HEAVY,
            padding=(1, 2),
            width=118,
        )

        return complex_panel

    def test_pickle_serialization(self, panel: Panel) -> dict:
        """Test pickle serialization of Rich Panel"""
        print("\n🥒 Testing Pickle Serialization...")

        try:
            # Serialize
            pickled_data = pickle.dumps(panel)
            pickled_string = base64.b64encode(pickled_data).decode("utf-8")

            print(f"✅ Pickle serialization successful")
            print(f"📏 Serialized size: {len(pickled_string)} characters")
            print(f"📝 Serialized data (first 200 chars): {pickled_string[:200]}...")

            # Deserialize
            decoded_data = base64.b64decode(pickled_string.encode("utf-8"))
            reconstructed_panel = pickle.loads(decoded_data)

            print(f"✅ Pickle deserialization successful")

            return {
                "method": "pickle",
                "success": True,
                "serialized_size": len(pickled_string),
                "serialized_data": pickled_string[:500],  # First 500 chars
                "reconstructed_object": reconstructed_panel,
                "error": None,
            }

        except Exception as e:
            print(f"❌ Pickle serialization failed: {e}")
            return {
                "method": "pickle",
                "success": False,
                "error": str(e),
                "serialized_size": 0,
                "serialized_data": None,
                "reconstructed_object": None,
            }

    def test_dill_serialization(self, panel: Panel) -> dict:
        """Test dill serialization of Rich Panel"""
        print("\n🌿 Testing Dill Serialization...")

        if not DILL_AVAILABLE:
            return {
                "method": "dill",
                "success": False,
                "error": "Dill not available",
                "serialized_size": 0,
                "serialized_data": None,
                "reconstructed_object": None,
            }

        try:
            # Serialize
            dill_data = dill.dumps(panel)
            dill_string = base64.b64encode(dill_data).decode("utf-8")

            print(f"✅ Dill serialization successful")
            print(f"📏 Serialized size: {len(dill_string)} characters")
            print(f"📝 Serialized data (first 200 chars): {dill_string[:200]}...")

            # Deserialize
            decoded_data = base64.b64decode(dill_string.encode("utf-8"))
            reconstructed_panel = dill.loads(decoded_data)

            print(f"✅ Dill deserialization successful")

            return {
                "method": "dill",
                "success": True,
                "serialized_size": len(dill_string),
                "serialized_data": dill_string[:500],  # First 500 chars
                "reconstructed_object": reconstructed_panel,
                "error": None,
            }

        except Exception as e:
            print(f"❌ Dill serialization failed: {e}")
            return {
                "method": "dill",
                "success": False,
                "error": str(e),
                "serialized_size": 0,
                "serialized_data": None,
                "reconstructed_object": None,
            }

    def test_rich_to_string_conversion(self, panel: Panel) -> dict:
        """Test Rich-to-string conversion (recommended approach)"""
        print("\n🎨 Testing Rich-to-String Conversion...")

        try:
            # Convert Rich object to string representation
            temp_console = Console(
                file=io.StringIO(),
                width=120,
                force_terminal=True,
                color_system="windows",
            )
            temp_console.print(panel)
            string_representation = temp_console.file.getvalue()

            print(f"✅ Rich-to-string conversion successful")
            print(f"📏 String size: {len(string_representation)} characters")
            print(f"📝 String representation (first 500 chars):")
            print(f"{string_representation[:500]}...")

            # Note: We can't reconstruct the original Panel from string,
            # but we can display the string representation

            return {
                "method": "rich_to_string",
                "success": True,
                "serialized_size": len(string_representation),
                "serialized_data": string_representation[:1000],  # First 1000 chars
                "reconstructed_object": string_representation,  # The string itself
                "error": None,
            }

        except Exception as e:
            print(f"❌ Rich-to-string conversion failed: {e}")
            return {
                "method": "rich_to_string",
                "success": False,
                "error": str(e),
                "serialized_size": 0,
                "serialized_data": None,
                "reconstructed_object": None,
            }

    def test_json_with_custom_encoding(self, panel: Panel) -> dict:
        """Test JSON serialization with custom Rich object encoding"""
        print("\n📄 Testing JSON with Custom Encoding...")

        try:
            # Custom encoder for Rich objects
            def encode_rich_object(obj):
                if hasattr(obj, "__rich_console__"):
                    temp_console = Console(file=io.StringIO(), width=120)
                    temp_console.print(obj)
                    return {
                        "type": "rich_object",
                        "class": obj.__class__.__name__,
                        "content": temp_console.file.getvalue(),
                    }
                else:
                    return {"type": "string", "content": str(obj)}

            # Serialize
            encoded_data = encode_rich_object(panel)
            json_string = json.dumps(encoded_data, indent=2)

            print(f"✅ JSON encoding successful")
            print(f"📏 JSON size: {len(json_string)} characters")
            print(f"📝 JSON data (first 300 chars):")
            print(f"{json_string[:300]}...")

            # Deserialize
            decoded_data = json.loads(json_string)

            print(f"✅ JSON decoding successful")
            print(f"🔍 Decoded type: {decoded_data['type']}")
            print(f"🏷️ Object class: {decoded_data.get('class', 'N/A')}")

            return {
                "method": "json_custom",
                "success": True,
                "serialized_size": len(json_string),
                "serialized_data": json_string[:800],  # First 800 chars
                "reconstructed_object": decoded_data,
                "error": None,
            }

        except Exception as e:
            print(f"❌ JSON encoding failed: {e}")
            return {
                "method": "json_custom",
                "success": False,
                "error": str(e),
                "serialized_size": 0,
                "serialized_data": None,
                "reconstructed_object": None,
            }

    def display_original_panel(self, panel: Panel):
        """Display the original complex panel"""
        print("\n" + "=" * 120)
        print("🎨 ORIGINAL COMPLEX RICH PANEL:")
        print("=" * 120)
        self.console.print(panel)
        print("=" * 120)

    def display_reconstructed_objects(self, results: list):
        """Display reconstructed objects from different serialization methods"""
        print("\n" + "🔄 RECONSTRUCTED OBJECTS COMPARISON:")
        print("=" * 120)

        for result in results:
            if result["success"] and result["reconstructed_object"]:
                print(f"\n📋 Method: {result['method'].upper()}")
                print("-" * 60)

                if result["method"] == "rich_to_string":
                    # For string representation, just show part of it
                    print("📝 String Representation (first 800 characters):")
                    print(result["reconstructed_object"][:800])
                    print("... [truncated]")

                elif result["method"] == "json_custom":
                    # For JSON, show the decoded structure
                    print("📄 JSON Decoded Structure:")
                    print(f"Type: {result['reconstructed_object']['type']}")
                    print(
                        f"Class: {result['reconstructed_object'].get('class', 'N/A')}"
                    )
                    print("Content (first 500 chars):")
                    print(result["reconstructed_object"]["content"][:500])
                    print("... [truncated]")

                else:
                    # For pickle/dill, try to display the reconstructed Panel
                    try:
                        print("🎨 Reconstructed Rich Panel:")
                        self.console.print(result["reconstructed_object"])
                    except Exception as e:
                        print(f"❌ Error displaying reconstructed object: {e}")
                        print(f"Object type: {type(result['reconstructed_object'])}")

                print("-" * 60)

    def run_all_tests(self):
        """Run all serialization tests"""
        print("🚀 Starting Rich Object Serialization Tests")
        print("=" * 120)

        # Create complex panel
        print("🏗️ Creating complex Rich Panel...")
        complex_panel = self.create_complex_panel()

        # Display original
        self.display_original_panel(complex_panel)

        # Run all serialization tests
        print("\n🧪 Running Serialization Tests...")

        results = []
        results.append(self.test_pickle_serialization(complex_panel))
        results.append(self.test_dill_serialization(complex_panel))
        results.append(self.test_rich_to_string_conversion(complex_panel))
        results.append(self.test_json_with_custom_encoding(complex_panel))

        self.test_results = results

        # Display results summary
        self.display_results_summary()

        # Display reconstructed objects
        self.display_reconstructed_objects(results)

        return results

    def display_results_summary(self):
        """Display a summary of all test results"""
        print("\n📊 SERIALIZATION TEST RESULTS SUMMARY:")
        print("=" * 120)

        # Create results table
        table = Table(title="🧪 Serialization Methods Comparison", box=DOUBLE)
        table.add_column("Method", style="cyan", no_wrap=True)
        table.add_column("Success", style="magenta")
        table.add_column("Size (chars)", justify="right", style="green")
        table.add_column("Reconstructable", style="yellow")
        table.add_column("Error", style="red")

        for result in self.test_results:
            success_icon = "✅" if result["success"] else "❌"
            size_str = str(result["serialized_size"]) if result["success"] else "N/A"

            # Determine if object can be reconstructed to original form
            if result["method"] in ["pickle", "dill"] and result["success"]:
                reconstructable = "✅ Full"
            elif (
                result["method"] in ["rich_to_string", "json_custom"]
                and result["success"]
            ):
                reconstructable = "⚠️ Partial"
            else:
                reconstructable = "❌ No"

            error_msg = (
                result.get("error", "")[:30] + "..."
                if result.get("error") and len(result.get("error", "")) > 30
                else result.get("error", "")
            )

            table.add_row(
                result["method"].title(),
                success_icon,
                size_str,
                reconstructable,
                error_msg or "None",
            )

        self.console.print(table)

        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        print("=" * 60)
        print(
            "🥒 Pickle: Best for full object reconstruction, but may fail with complex Rich objects"
        )
        print("🌿 Dill: More robust than pickle, handles more object types")
        print(
            "🎨 Rich-to-String: Recommended for socket transmission - preserves visual formatting"
        )
        print("📄 JSON Custom: Good for structured data, partial reconstruction only")
        print(
            "\n🎯 For your socket error transmission use case: Rich-to-String is recommended!"
        )


def main():
    """Main test function"""
    print("🎨 Rich Object Serialization Test Suite")
    print("=" * 120)

    tester = RichSerializationTester()
    results = tester.run_all_tests()

    print("\n🎉 All tests completed!")
    print(f"📊 Total methods tested: {len(results)}")
    print(f"✅ Successful methods: {sum(1 for r in results if r['success'])}")
    print(f"❌ Failed methods: {sum(1 for r in results if not r['success'])}")

    return results


if __name__ == "__main__":
    main()
