#!/usr/bin/env python3
"""
Configuration helper for LangGraph Chatbot system_logging
Helps you set up the best system_logging configuration for your needs
"""

from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

from src.config import settings


def show_current_config():
    """Show current system_logging configuration"""
    console = settings.console
    console.print(Panel.fit("🔧 Current Logging Configuration", style="bold blue"))

    # Read current config
    try:
        import config

        console.print(f"✅ ENABLE_SOCKET_LOGGING: {config.ENABLE_SOCKET_LOGGING}")
        console.print(f"✅ SOCKET_HOST: {config.SOCKET_HOST}")
        console.print(f"✅ SOCKET_PORT: {config.SOCKET_PORT}")
        console.print(f"✅ LOG_DISPLAY_MODE: {config.LOG_DISPLAY_MODE}")
    except Exception as e:
        console.print(f"❌ Error reading config: {e}")


def recommend_configuration():
    """Recommend the best configuration based on user needs"""
    console = settings.console
    console.print("\n🎯 Let's find the best system_logging setup for you!")

    # Ask about use case
    use_case = Prompt.ask(
        "What's your primary use case?",
        choices=["development", "production", "debugging", "learning"],
        default="development",
    )

    # Ask about visibility preference
    want_visible_logs = Confirm.ask(
        "Do you want to see logs in real-time?", default=True
    )

    # Ask about performance
    performance_critical = Confirm.ask(
        "Is performance critical (minimal overhead)?", default=False
    )

    # Make recommendations
    console.print("\n💡 Recommendations based on your needs:")

    if use_case == "development" and want_visible_logs:
        recommended_mode = "separate_window"
        console.print("🪟 **Recommended: separate_window**")
        console.print("   ✅ Perfect for development")
        console.print("   ✅ Logs visible in separate console")
        console.print("   ✅ Doesn't clutter main application")

    elif use_case == "production" and not performance_critical:
        recommended_mode = "file"
        console.print("📄 **Recommended: file**")
        console.print("   ✅ Good for production")
        console.print("   ✅ Logs saved for later analysis")
        console.print("   ✅ Clean user interface")

    elif performance_critical:
        recommended_mode = "background"
        console.print("🔇 **Recommended: background**")
        console.print("   ✅ Minimal performance impact")
        console.print("   ✅ Clean interface")
        console.print("   ⚠️ Logs not visible (use for production)")

    else:
        recommended_mode = "separate_window"
        console.print("🪟 **Recommended: separate_window**")
        console.print("   ✅ Good default choice")
        console.print("   ✅ Visible logs for monitoring")

    return recommended_mode


def update_config_file(new_mode):
    """Update the config.py file with new system_logging mode"""
    console = settings.console
    config_path = "config.py"
    from pathlib import Path

    try:
        # Read current config
        with Path(config_path).open("r") as f:
            content = f.read()

        # Update LOG_DISPLAY_MODE
        if "LOG_DISPLAY_MODE" in content:
            # Replace existing setting
            import re

            pattern = r'LOG_DISPLAY_MODE\s*=\s*[^"\n]*"[^"]*"'
            replacement = (
                f'LOG_DISPLAY_MODE = os.getenv("LOG_DISPLAY_MODE", "{new_mode}")'
            )
            content = re.sub(pattern, replacement, content)
        else:
            # Add new setting
            content += (
                f'\nLOG_DISPLAY_MODE = os.getenv("LOG_DISPLAY_MODE", "{new_mode}")\n'
            )

        # Write back
        with Path(config_path).open("w") as f:
            f.write(content)

        console.print(f"✅ Updated config.py with LOG_DISPLAY_MODE = '{new_mode}'")
        return True

    except Exception as e:
        console.print(f"❌ Error updating config file: {e}")
        return False


def test_configuration():
    """Test the current system_logging configuration"""
    console = settings.console
    console.print("\n🧪 Testing current configuration...")

    try:
        from src.utils.socket_manager import socket_manager

        # Test connection
        socket_con = socket_manager.get_socket_connection()

        if socket_con:
            console.print("✅ Socket connection established")

            # Send test message
            test_msg = "🧪 Configuration test message"
            socket_con.send_error(f"[CONFIG TEST] {test_msg}")
            console.print("✅ Test message sent")

            # Check subprocess
            if socket_manager.is_log_server_running():
                pid = socket_manager._log_server_process.pid
                console.print(f"✅ Log server running (PID: {pid})")
            else:
                console.print("⚠️ Log server subprocess not detected")

            console.print("✅ Configuration test passed!")

        else:
            console.print("❌ Failed to establish socket connection")
            console.print("💡 Check your ENABLE_SOCKET_LOGGING setting")

    except Exception as e:
        console.print(f"❌ Configuration test failed: {e}")


def show_troubleshooting():
    """Show troubleshooting tips"""
    console = settings.console
    console.print("\n🔧 Troubleshooting Tips")

    table = Table(title="Common Issues and Solutions")
    table.add_column("Issue", style="red")
    table.add_column("Solution", style="green")

    table.add_row(
        "Logs not visible", "Set LOG_DISPLAY_MODE='separate_window' in config.py"
    )
    table.add_row("No socket connection", "Set ENABLE_SOCKET_LOGGING=True in config.py")
    table.add_row(
        "Port already in use", "Change SOCKET_PORT in config.py or stop other processes"
    )
    table.add_row("Subprocess won't start", "Check file permissions and Python path")
    table.add_row(
        "Performance issues", "Set LOG_DISPLAY_MODE='background' for production"
    )

    console.print(table)


def main():
    """Main configuration helper"""
    console = settings.console
    console.print("=" * 80)
    console.print("🔧 LANGGRAPH CHATBOT - LOGGING CONFIGURATION")
    console.print("=" * 80)

    show_current_config()

    console.print("\n🎯 Configuration Options:")
    console.print("1. Show current configuration")
    console.print("2. Get personalized recommendations")
    console.print("3. Update configuration")
    console.print("4. Test current configuration")
    console.print("5. Show troubleshooting tips")
    console.print("6. Exit")

    while True:
        try:
            choice = Prompt.ask(
                "Choose an option", choices=["1", "2", "3", "4", "5", "6"], default="2"
            )

            if choice == "1":
                show_current_config()

            elif choice == "2":
                recommended_mode = recommend_configuration()
                if Confirm.ask(
                    f"\nApply recommended setting ({recommended_mode})?", default=True
                ):
                    if update_config_file(recommended_mode):
                        console.print(
                            "✅ Configuration updated! Restart your application to apply changes."
                        )

            elif choice == "3":
                new_mode = Prompt.ask(
                    "Choose log display mode",
                    choices=["separate_window", "background", "file", "console"],
                    default="separate_window",
                )
                if update_config_file(new_mode):
                    console.print("✅ Configuration updated!")

            elif choice == "4":
                test_configuration()

            elif choice == "5":
                show_troubleshooting()

            elif choice == "6":
                break

        except KeyboardInterrupt:
            break

    console.print("\n👋 Configuration helper complete!")
    console.print("💡 Remember to restart your application after changing settings")


if __name__ == "__main__":
    main()
