"""
Test file for prompt_toolkit autocomplete.

Run this file directly to test:
    python tests/test_prompt_toolkit_autocomplete.py

You should see:
1. A beautiful styled prompt (➜)
2. When you type "/" you'll see autocomplete dropdown
3. Commands like /help, /agent, /clear, /exit with emojis
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import sys
from pathlib import Path

# Add project root to path

# First, register the slash commands (normally done by ChatInitializer)
from src.slash_commands.on_run_time_register import OnRunTimeRegistry
from src.slash_commands.protocol import SlashCommand


def register_test_commands():
    """Register some test commands for autocomplete."""
    registry = OnRunTimeRegistry()

    test_commands = [
        SlashCommand(
            command="help",
            options=None,
            requirements=None,
            description="Show available commands and usage",
            handler=None
        ),
        SlashCommand(
            command="agent",
            options=None,
            requirements=None,
            description="Invoke AI agent for complex tasks",
            handler=None
        ),
        SlashCommand(
            command="clear",
            options=None,
            requirements=None,
            description="Clear conversation history",
            handler=None
        ),
        SlashCommand(
            command="exit",
            options=None,
            requirements=None,
            description="Exit the application",
            handler=None
        ),
        SlashCommand(
            command="chat",
            options=None,
            requirements=None,
            description="Normal chat mode",
            handler=None
        ),
        SlashCommand(
            command="tool",
            options=None,
            requirements=None,
            description="Use a specific tool",
            handler=None
        ),
    ]

    for cmd in test_commands:
        try:
            registry.register(cmd)
            print(f"  ✓ Registered: /{cmd.command}")
        except Exception as e:
            # Already registered (singleton)
            print(f"  ⚠ Already registered: /{cmd.command}")


def main():
    print("=" * 60)
    print("  🎨 prompt_toolkit Autocomplete Test")
    print("=" * 60)
    print()
    print("📝 Registering test commands...")
    register_test_commands()
    print()
    print("=" * 60)
    print("  Type '/' to see autocomplete suggestions!")
    print("  Type '/exit' or Ctrl+C to quit")
    print("=" * 60)
    print()

    # Now test the InputHandler
    from src.ui.chatInputHandler import InputHandler

    handler = InputHandler()

    while True:
        try:
            user_input = handler.get_user_input()

            print(f"\n  📨 You entered: {user_input}\n")

            if user_input in ['/exit', 'exit']:
                print("  👋 Goodbye!")
                break

        except KeyboardInterrupt:
            print("\n  👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n  ❌ Error: {e}\n")
            break


if __name__ == "__main__":
    main()

