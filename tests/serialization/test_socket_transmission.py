#!/usr/bin/env python3
"""
Socket Transmission Test for Rich Objects

This module tests actual socket transmission of serialized Rich objects,
simulating the real-world scenario of sending Rich Panel objects from
the main process to the debug process.
"""

import sys
import os
import socket
import threading
import time
import json
import base64
import pickle
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
from rich.box import DOUBLE, HEAVY
from rich.rule import Rule
from rich.align import Align

# Try to import dill
try:
    import dill

    DILL_AVAILABLE = True
except ImportError:
    DILL_AVAILABLE = False


class MockSocketServer:
    """Mock socket server to simulate debug window process"""

    def __init__(self, host="localhost", port=5391):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.received_messages = []
        self.console = Console(width=120, force_terminal=True)

    def start_server(self):
        """Start the mock socket server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            self.server_socket.settimeout(1)  # Non-blocking accept
            self.running = True

            print(f"🚀 Mock server started on {self.host}:{self.port}")

            while self.running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    print(f"📡 Connection from {addr}")

                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client, args=(client_socket,)
                    )
                    client_thread.daemon = True
                    client_thread.start()

                except socket.timeout:
                    continue  # Check if still running
                except Exception as e:
                    if self.running:
                        print(f"❌ Server error: {e}")
                    break

        except Exception as e:
            print(f"❌ Failed to start server: {e}")
        finally:
            self.cleanup()

    def handle_client(self, client_socket):
        """Handle client connection"""
        try:
            while self.running:
                data = client_socket.recv(1024 * 1024)  # 1MB buffer
                if not data:
                    break

                message = data.decode("utf-8")
                self.received_messages.append(message)

                print(f"\n📨 Received message ({len(message)} chars)")
                print("=" * 80)

                # Try to detect message type and display appropriately
                self.display_received_message(message)

        except Exception as e:
            print(f"❌ Client handling error: {e}")
        finally:
            client_socket.close()

    def display_received_message(self, message):
        """Display received message with appropriate formatting"""
        try:
            # Check if it's JSON
            if message.strip().startswith("{"):
                try:
                    json_data = json.loads(message)
                    if json_data.get("type") == "rich_object":
                        print("📄 JSON-encoded Rich object received:")
                        print(f"Class: {json_data.get('class', 'Unknown')}")
                        print("Content:")
                        print(
                            json_data.get("content", "")[:500] + "..."
                            if len(json_data.get("content", "")) > 500
                            else json_data.get("content", "")
                        )
                        return
                except:
                    pass

            # Check if it's base64 encoded (pickle/dill)
            if (
                len(message) > 100
                and message.replace("\n", "").replace("=", "").isalnum()
            ):
                try:
                    decoded = base64.b64decode(message.encode("utf-8"))
                    # Try pickle first
                    try:
                        obj = pickle.loads(decoded)
                        print(
                            "🥒 Pickle-encoded Rich object received and reconstructed:"
                        )
                        self.console.print(obj)
                        return
                    except:
                        pass

                    # Try dill if available
                    if DILL_AVAILABLE:
                        try:
                            obj = dill.loads(decoded)
                            print(
                                "🌿 Dill-encoded Rich object received and reconstructed:"
                            )
                            self.console.print(obj)
                            return
                        except:
                            pass

                    print("📦 Base64-encoded data received (unknown format)")
                    print(f"Size: {len(decoded)} bytes")
                    return
                except:
                    pass

            # Assume it's a Rich string representation
            print("🎨 Rich string representation received:")
            print(message[:1000] + "..." if len(message) > 1000 else message)

        except Exception as e:
            print(f"❌ Error displaying message: {e}")
            print("Raw message (first 200 chars):")
            print(message[:200])

    def stop_server(self):
        """Stop the mock server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()

    def cleanup(self):
        """Cleanup server resources"""
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        print("🧹 Mock server cleaned up")


class SocketTransmissionTester:
    """Test socket transmission of Rich objects"""

    def __init__(self):
        self.console = Console(width=120, force_terminal=True)
        self.server = None
        self.server_thread = None

    def create_test_panel(self) -> Panel:
        """Create a test Rich Panel for transmission"""

        # Create a table with error information
        error_table = Table(title="🚨 Error Details", box=DOUBLE)
        error_table.add_column("Property", style="cyan")
        error_table.add_column("Value", style="red")

        error_table.add_row("Error Type", "ValueError")
        error_table.add_row("Message", "Agent response must be a dictionary")
        error_table.add_row("File", "agent_mode_node.py")
        error_table.add_row("Line", "285")
        error_table.add_row("Function", "start")
        error_table.add_row("Context", "AI Parameter Generation")

        # Create code snippet
        code_snippet = """
def start(self, index: int = 0) -> 'Agent':
    try:
        response = agent_ai.invoke([
            settings.HumanMessage(content=prompt[0]),
            settings.HumanMessage(content=prompt[1])
        ])
        response = ModelManager.convert_to_json(response)
        if not isinstance(response, dict):  # ← ERROR HERE
            raise ValueError("Agent response must be a dictionary")
    except Exception as e:
        RichTracebackManager.handle_exception(e, context="AI Parameter Generation")
        raise
"""

        syntax = Syntax(code_snippet, "python", theme="monokai", line_numbers=True)

        # Create the complex panel
        content = [
            Align.center(Text("🚨 SOCKET TRANSMISSION TEST ERROR", style="bold red")),
            Rule("📊 Error Information", style="red"),
            error_table,
            Rule("💻 Code Context", style="yellow"),
            syntax,
            Rule("🔧 Debug Info", style="blue"),
            Text("Timestamp: 2025-01-13 15:45:30", style="dim"),
            Text("Process: Main Process (PID: 12345)", style="dim"),
            Text("Thread: MainThread", style="dim"),
            Text("Memory: 156.7 MB", style="dim"),
        ]

        from rich.console import Group

        content_group = Group(*content)

        panel = Panel(
            content_group,
            title="🚨 RICH TRACEBACK - SOCKET TRANSMISSION TEST",
            subtitle="Testing serialization and socket transmission of complex Rich Panel",
            border_style="bright_red",
            box=HEAVY,
            padding=(1, 2),
            width=118,
        )

        return panel

    def start_mock_server(self):
        """Start the mock debug server"""
        self.server = MockSocketServer()
        self.server_thread = threading.Thread(target=self.server.start_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        time.sleep(1)  # Give server time to start

    def stop_mock_server(self):
        """Stop the mock debug server"""
        if self.server:
            self.server.stop_server()
        if self.server_thread:
            self.server_thread.join(timeout=2)

    def send_via_socket(self, data: str, method_name: str):
        """Send data via socket to mock server"""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)
            client_socket.connect(("localhost", 5391))

            print(f"📤 Sending {method_name} data ({len(data)} chars)...")
            client_socket.sendall(data.encode("utf-8"))

            client_socket.close()
            print(f"✅ {method_name} data sent successfully")

        except Exception as e:
            print(f"❌ Failed to send {method_name} data: {e}")

    def test_pickle_transmission(self, panel: Panel):
        """Test pickle serialization and socket transmission"""
        print("\n🥒 Testing Pickle Transmission...")
        print("-" * 60)

        try:
            # Serialize with pickle
            pickled_data = pickle.dumps(panel)
            pickled_string = base64.b64encode(pickled_data).decode("utf-8")

            print(f"✅ Pickle serialization: {len(pickled_string)} chars")

            # Send via socket
            self.send_via_socket(pickled_string, "Pickle")

        except Exception as e:
            print(f"❌ Pickle transmission failed: {e}")

    def test_dill_transmission(self, panel: Panel):
        """Test dill serialization and socket transmission"""
        print("\n🌿 Testing Dill Transmission...")
        print("-" * 60)

        if not DILL_AVAILABLE:
            print("⚠️ Dill not available, skipping test")
            return

        try:
            # Serialize with dill
            dill_data = dill.dumps(panel)
            dill_string = base64.b64encode(dill_data).decode("utf-8")

            print(f"✅ Dill serialization: {len(dill_string)} chars")

            # Send via socket
            self.send_via_socket(dill_string, "Dill")

        except Exception as e:
            print(f"❌ Dill transmission failed: {e}")

    def test_rich_string_transmission(self, panel: Panel):
        """Test Rich-to-string conversion and socket transmission"""
        print("\n🎨 Testing Rich String Transmission...")
        print("-" * 60)

        try:
            # Convert to string
            import io

            temp_console = Console(
                file=io.StringIO(),
                width=120,
                force_terminal=True,
                color_system="windows",
            )
            temp_console.print(panel)
            string_data = temp_console.file.getvalue()

            print(f"✅ Rich-to-string conversion: {len(string_data)} chars")

            # Send via socket
            self.send_via_socket(string_data, "Rich String")

        except Exception as e:
            print(f"❌ Rich string transmission failed: {e}")

    def test_json_transmission(self, panel: Panel):
        """Test JSON encoding and socket transmission"""
        print("\n📄 Testing JSON Transmission...")
        print("-" * 60)

        try:
            # Convert to JSON
            import io

            temp_console = Console(file=io.StringIO(), width=120)
            temp_console.print(panel)

            json_data = {
                "type": "rich_object",
                "class": panel.__class__.__name__,
                "content": temp_console.file.getvalue(),
                "timestamp": time.time(),
                "method": "json_transmission_test",
            }

            json_string = json.dumps(json_data, indent=2)

            print(f"✅ JSON encoding: {len(json_string)} chars")

            # Send via socket
            self.send_via_socket(json_string, "JSON")

        except Exception as e:
            print(f"❌ JSON transmission failed: {e}")

    def run_transmission_tests(self):
        """Run all socket transmission tests"""
        print("🚀 Starting Socket Transmission Tests")
        print("=" * 120)

        # Create test panel
        print("🏗️ Creating test Rich Panel...")
        test_panel = self.create_test_panel()

        # Display original panel
        print("\n🎨 ORIGINAL PANEL TO TRANSMIT:")
        print("=" * 80)
        self.console.print(test_panel)
        print("=" * 80)

        # Start mock server
        print("\n🚀 Starting mock debug server...")
        self.start_mock_server()

        try:
            # Run transmission tests
            print("\n📡 Running Socket Transmission Tests...")

            self.test_pickle_transmission(test_panel)
            time.sleep(1)  # Give server time to process

            self.test_dill_transmission(test_panel)
            time.sleep(1)

            self.test_rich_string_transmission(test_panel)
            time.sleep(1)

            self.test_json_transmission(test_panel)
            time.sleep(1)

            print("\n✅ All transmission tests completed!")
            print(
                f"📊 Total messages received by server: {len(self.server.received_messages)}"
            )

        finally:
            # Stop mock server
            print("\n🛑 Stopping mock server...")
            self.stop_mock_server()


def main():
    """Main test function"""
    print("📡 Socket Transmission Test Suite for Rich Objects")
    print("=" * 120)

    tester = SocketTransmissionTester()
    tester.run_transmission_tests()

    print("\n🎉 Socket transmission tests completed!")
    print("\n💡 CONCLUSIONS:")
    print("=" * 60)
    print(
        "🥒 Pickle: Can reconstruct original Rich objects, but may fail with complex objects"
    )
    print("🌿 Dill: More robust reconstruction, handles complex Rich objects better")
    print("🎨 Rich String: Best for visual representation, no reconstruction needed")
    print("📄 JSON: Good for structured data with metadata, partial reconstruction")
    print("\n🎯 RECOMMENDATION: Use Rich-to-String for your error transmission system!")


if __name__ == "__main__":
    main()
