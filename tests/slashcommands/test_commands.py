#!/usr/bin/env python3
"""
Test script to verify command registration works.
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

from src.slash_commands.commands.clear import register_clear_command
from src.slash_commands.commands.help import register_help_command
from src.slash_commands.commands.core_slashs.agent import register_agent_command
from src.slash_commands.on_run_time_register import OnRunTimeRegistry


def test_registration():
    """Test that commands can be registered."""
    print("Testing command registration...")
    
    # Register commands
    register_clear_command()
    register_help_command()
    register_agent_command()
    
    # Check registry
    registry = OnRunTimeRegistry()
    print(f"Number of registered commands: {len(registry)}")
    
    # List registered commands
    for cmd in registry._registered_commands:
        print(f"  /{cmd.command} - {cmd.description}")
    
    # Test getting specific commands
    try:
        clear_cmd = registry.get("clear")
        print(f"SUCCESS: Successfully retrieved /{clear_cmd.command}")
    except Exception as e:
        print(f"ERROR: Failed to get /clear: {e}")
    
    try:
        help_cmd = registry.get("help")
        print(f"SUCCESS: Successfully retrieved /{help_cmd.command}")
    except Exception as e:
        print(f"ERROR: Failed to get /help: {e}")
    
    print("Registration test complete!")


if __name__ == "__main__":
    test_registration()


if __name__ == "__main__":
    test_registration()