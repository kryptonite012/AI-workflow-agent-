#!/usr/bin/env python3
"""
Log Viewer Demo - Shows different ways to view logs from your LangGraph application
"""

import os
import time

import config
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from utils.socket_manager import socket_manager

from src.config import settings


def show_log_display_options():
    """Show all available log display options"""
    console = settings.console
    console.print(
        Panel.fit(
            Text("📊 Log Display Options", style="bold magenta"),
            title="LangGraph Chatbot - Log Viewing",
            style="bold blue",
        )
    )

    table = Table(title="Available Log Display Modes")
    table.add_column("Mode", style="cyan", no_wrap=True)
    table.add_column("Description", style="green")
    table.add_column("Best For", style="yellow")
    table.add_column("Visibility", style="red")

    table.add_row(
        "separate_window",
        "Opens log server in separate console window",
        "Development, debugging",
        "✅ Fully visible",
    )
    table.add_row(
        "background",
        "Runs log server silently in background",
        "Production, clean interface",
        "❌ Not visible",
    )
    table.add_row(
        "file",
        "Logs to socket_server.log file",
        "Production, log analysis",
        "📄 File-based",
    )
    table.add_row(
        "console",
        "Shows logs in same console (mixed output)",
        "Quick testing",
        "⚠️ Mixed with app output",
    )

    console.print(table)

    console.print(
        f"\n📋 Current setting: LOG_DISPLAY_MODE = '{config.LOG_DISPLAY_MODE}'"
    )
    console.print(
        "💡 Change this in config.py or set environment variable LOG_DISPLAY_MODE"
    )


def demo_separate_window():
    """Demo the separate window log display"""
    console = settings.console
    console.print("\n🪟 Demonstrating Separate Window Mode...")
    console.print("   This will open a new console window for logs")

    # Temporarily set to separate window mode
    original_mode = config.LOG_DISPLAY_MODE
    config.LOG_DISPLAY_MODE = "separate_window"

    try:
        socket_con = socket_manager.get_socket_connection()

        if socket_con:
            console.print("✅ Log server opened in separate window!")
            console.print(
                "👀 Check for a new console window titled 'LangGraph Log Server'"
            )

            # Send some demo messages
            demo_messages = [
                "🪟 Separate Window Demo Message 1",
                "🪟 Separate Window Demo Message 2",
                "🪟 Separate Window Demo Message 3",
            ]

            for i, msg in enumerate(demo_messages, 1):
                console.print(f"   Sending message {i} to separate window...")
                socket_con.send_error(f"[SEPARATE WINDOW] {msg}")
                time.sleep(1)

            console.print("✅ Messages sent! Check the separate console window.")

        else:
            console.print("❌ Failed to start separate window log server")

    finally:
        config.LOG_DISPLAY_MODE = original_mode


def demo_file_logging():
    """Demo the file-based log display"""
    console = settings.console
    console.print("\n📄 Demonstrating File Logging Mode...")

    # Temporarily set to file mode
    original_mode = config.LOG_DISPLAY_MODE
    config.LOG_DISPLAY_MODE = "file"

    # Reset socket connection to force new mode
    socket_manager.close_connection()
    socket_manager._socket_con = None
    socket_manager._log_server_process = None

    try:
        socket_con = socket_manager.get_socket_connection()

        if socket_con:
            log_file_path = os.path.join(
                os.path.dirname(__file__), "utils", "socket_server.log"
            )
            console.print(f"✅ Log server started with file system_logging!")
            console.print(f"📄 Logs will be written to: {log_file_path}")

            # Send some demo messages
            demo_messages = [
                "📄 File Logging Demo Message 1",
                "📄 File Logging Demo Message 2",
                "📄 File Logging Demo Message 3",
            ]

            for i, msg in enumerate(demo_messages, 1):
                console.print(f"   Sending message {i} to log file...")
                socket_con.send_error(f"[FILE LOGGING] {msg}")
                time.sleep(0.5)

            console.print("✅ Messages sent to log file!")

            # Try to show file contents
            time.sleep(1)
            if os.path.exists(log_file_path):
                console.print(f"\n📖 Log file contents:")
                try:
                    with open(log_file_path, "r") as f:
                        content = f.read()
                        if content.strip():
                            console.print(
                                Panel(content, title="socket_server.log", style="green")
                            )
                        else:
                            console.print("📄 Log file is empty (logs may be buffered)")
                except Exception as e:
                    console.print(f"❌ Could not read log file: {e}")
            else:
                console.print("📄 Log file not found yet (may be created later)")

        else:
            console.print("❌ Failed to start file system_logging server")

    finally:
        config.LOG_DISPLAY_MODE = original_mode


def show_current_logs():
    """Show what logs are currently being generated"""
    console = settings.console
    console.print("\n📊 Current Log Activity...")

    socket_con = socket_manager.get_socket_connection()

    if socket_con:
        console.print("✅ Log server is active")

        if socket_manager.is_log_server_running():
            pid = socket_manager._log_server_process.pid
            console.print(f"🔄 Log server process ID: {pid}")
            console.print(f"📺 Display mode: {config.LOG_DISPLAY_MODE}")

            # Send a test message
            test_msg = f"🧪 Test log message at {time.strftime('%H:%M:%S')}"
            socket_con.send_error(f"[LOG VIEWER] {test_msg}")
            console.print(f"📤 Sent test message: {test_msg}")

        else:
            console.print("⚠️ Log server process not detected")
    else:
        console.print("❌ No active log server connection")


def interactive_log_demo():
    """Interactive demo where user can send custom log messages"""
    console = settings.console
    console.print("\n🎮 Interactive Log Demo")
    console.print("Type messages to send to the log server (type 'quit' to exit)")

    socket_con = socket_manager.get_socket_connection()

    if not socket_con:
        console.print("❌ No log server connection available")
        return

    console.print("✅ Ready to send messages!")
    console.print("💡 Your messages will appear in the log server window/file")

    message_count = 0
    while True:
        try:
            user_input = input("\n📝 Enter log message (or 'quit'): ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                break

            if user_input:
                message_count += 1
                socket_con.send_error(
                    f"[USER MESSAGE {message_count:02d}] {user_input}"
                )
                console.print(f"✅ Message sent to log server!")
            else:
                console.print("⚠️ Empty message, try again")

        except KeyboardInterrupt:
            break

    console.print(f"\n✅ Interactive demo complete! Sent {message_count} messages.")


def main():
    """Main log viewer demo"""
    console = settings.console
    console.print("=" * 80)
    console.print("📊 LANGGRAPH CHATBOT - LOG VIEWER DEMO")
    console.print("=" * 80)

    show_log_display_options()

    console.print("\n🎯 Demo Options:")
    console.print("1. Show current log activity")
    console.print("2. Demo separate window system_logging")
    console.print("3. Demo file-based system_logging")
    console.print("4. Interactive log demo")
    console.print("5. Show all options and exit")

    while True:
        try:
            choice = input("\n🤔 Choose demo (1-5): ").strip()

            if choice == "1":
                show_current_logs()
            elif choice == "2":
                demo_separate_window()
            elif choice == "3":
                demo_file_logging()
            elif choice == "4":
                interactive_log_demo()
            elif choice == "5":
                show_log_display_options()
                break
            else:
                console.print("❌ Invalid choice, please enter 1-5")
                continue

            input("\n⏸️ Press Enter to continue...")

        except KeyboardInterrupt:
            break

    # Cleanup
    console.print("\n🧹 Cleaning up...")
    socket_manager.close_connection()
    console.print("✅ Demo complete!")


if __name__ == "__main__":
    main()
