#!/usr/bin/env python3
"""
Test script to verify ExecutionAr works correctly.
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

from src.slash_commands.executionar import ExecutionAr
from src.slash_commands.parser import ParseCommand
from src.slash_commands.commands.clear import register_clear_command
from src.slash_commands.commands.help import register_help_command
from src.slash_commands.protocol import CommandOption, SlashCommand


def test_executionar():
    """Test that ExecutionAr works correctly."""
    print("Testing ExecutionAr...")
    
    # Register commands first
    register_clear_command()
    register_help_command()
    
    # Create executor
    executor = ExecutionAr()
    
    # Test 1: Execute help command directly
    print("\n1. Testing direct execution of /help...")
    help_command = SlashCommand(command="help", options=None, requirements=None, description=None, handler=None)
    result = executor.execute(help_command)
    print(f"   Result: {result.success}")
    print(f"   Message: {result.message[:100]}...")  # Truncate long message
    
    # Test 2: Execute clear command directly
    print("\n2. Testing direct execution of /clear...")
    clear_command = SlashCommand(command="clear", options=None, requirements=None, description=None, handler=None)
    result = executor.execute(clear_command)
    print(f"   Result: {result.success}")
    print(f"   Message: {result.message}")
    
    # Test 3: Execute non-existent command
    print("\n3. Testing non-existent command...")
    nonexistent_command = SlashCommand(command="nonexistent", options=None, requirements=None, description=None, handler=None)
    result = executor.execute(nonexistent_command)
    print(f"   Result: {result.success}")
    print(f"   Message: {result.message}")
    
    # Test 4: Execute with options (if we add this capability later)
    print("\n4. Testing execution with options...")
    option = CommandOption(name="command", value=["clear"])
    help_with_option = SlashCommand(command="help", options=[option], requirements=None, description=None, handler=None)
    result = executor.execute(help_with_option)
    print(f"   Result: {result.success}")
    print(f"   Message: {result.message[:100]}...")  # Truncate long message
    
    print("\nExecutionAr tests complete!")


if __name__ == "__main__":
    test_executionar()