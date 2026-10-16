#!/usr/bin/env python3
"""
Test script to verify the full flow: User Input -> Parser -> ExecutionAr.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import sys
import os
import time

# Add the project root to Python path
start_time = time.perf_counter()
from src.slash_commands.executionar import ExecutionAr
from src.slash_commands.parser import ParseCommand
from src.slash_commands.commands.clear import register_clear_command
from src.slash_commands.commands.help import register_help_command
from src.slash_commands.commands.core_slashs.agent import register_agent_command

def test_full_flow():
    """Test the full flow from user input to execution."""
    print("Testing full flow: User Input -> Parser -> ExecutionAr")
    
    # Register commands first
    register_clear_command()
    register_help_command()
    register_agent_command()
    
    # Create parser and executor
    parser = ParseCommand()
    executor = ExecutionAr()
    
    # Test cases
    test_cases = [
        "/help",
        "/clear",
        "/help --command clear",
        "/nonexistent",
        "/agent --high tell me a joke",
    ]
    for i, user_input in enumerate(test_cases, 1):
        print(f"\n{i}. Testing user input: '{user_input}'")
        
        try:
            # Step 1: Parse user input
            print("   Step 1: Parsing user input...")
            parsed_command = parser.get_command(user_input)
            print(f"   Parsed: command='{parsed_command.command}', options={len(parsed_command.options) if parsed_command.options else 0}")
            
            # Step 2: Execute parsed command
            print("   Step 2: Executing parsed command...")
            result = executor.execute(parsed_command)
            print(f"   Result: {'SUCCESS' if result.success else 'FAILED'}")
            print(f"   Message: {result.message[:100]}{'...' if len(result.message) > 100 else ''}")
            
        except Exception as e:
            print(f"   ERROR: {e}")
    
    print("\nFull flow tests complete! in {:.4f} seconds.".format(time.perf_counter() - start_time))


# Add the missing method to ExecutionAr class
def add_execute_parsed_method():
    """Add the missing execute_parsed method to ExecutionAr."""
    # We'll add this method to make the full flow work
    pass


if __name__ == "__main__":
    test_full_flow()