#!/usr/bin/env python3
"""
Test script to verify command handlers work correctly.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import sys
import os

# Add the project root to Python path

from src.slash_commands.commands.clear import register_clear_command, clear_handler
from src.slash_commands.commands.help import register_help_command, help_handler
from src.slash_commands.commands.core_slashs.agent import register_agent_command
from src.slash_commands.on_run_time_register import OnRunTimeRegistry
from src.slash_commands.protocol import SlashCommand, CommandOption, CommandResult


def test_handlers():
    """Test that command handlers work correctly."""
    print("Testing command handlers...")
    
    # Register commands
    register_clear_command()
    register_help_command()
    register_agent_command()
    
    # Get registered commands
    registry = OnRunTimeRegistry()
    clear_command = registry.get("clear")
    help_command = registry.get("help")
    
    # Test clear handler
    print("\nTesting clear handler...")
    try:
        result = clear_handler(clear_command, None)
        print(f"Clear handler result: {result.success} - {result.message}")
    except Exception as e:
        print(f"Error in clear handler: {e}")
    
    # Test help handler - general help
    print("\nTesting help handler (general)...")
    try:
        result = help_handler(help_command, None)
        print(f"Help handler result: {result.success}")
        print(f"Help message:\n{result.message}")
    except Exception as e:
        print(f"Error in help handler: {e}")
    
    # Test help handler - specific command help
    print("\nTesting help handler (specific command)...")
    try:
        # Create a mock option for "clear" command
        option = CommandOption(name="clear", value=None)
        result = help_handler(help_command, option)
        print(f"Specific help result: {result.success}")
        print(f"Specific help message:\n{result.message}")
    except Exception as e:
        print(f"Error in specific help handler: {e}")
    
    print("\nHandler tests complete!")


if __name__ == "__main__":
    test_handlers()