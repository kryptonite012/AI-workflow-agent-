import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


#!/usr/bin/env python3
"""Test script to verify MCP fixes"""

import sys
import os


from src.mcp.load_config import McpConfigFile
from src.mcp.mcp_register_structure import Command


def test_command_enum():
    print("=== Testing Command Enum ===")
    print(f"Command.NPX = {Command.NPX}")
    print(f"str(Command.NPX) = {str(Command.NPX)}")
    print(f"Type of Command.NPX: {type(Command.NPX)}")
    return True


def test_config_loading():
    print("\n=== Testing Config Loading ===")
    try:
        configs = McpConfigFile.retrieve_config()
        if configs:
            print(f"? Loaded {len(configs)} server configs")
            for i, config in enumerate(configs):
                cmd = config.get("command")
                print(
                    f"  Server {i + 1}: {config.get('name')} -> {cmd} (type: {type(cmd)})"
                )
            return True
        else:
            print("? No configs loaded")
            return False
    except Exception as e:
        print(f"? Config loading failed: {e}")
        return False


def test_command_conversion():
    print("\n=== Testing Command Conversion ===")
    try:
        configs = McpConfigFile.retrieve_config()
        if configs and len(configs) > 0:
            first_config = configs[0]
            cmd = first_config.get("command")
            cmd_str = str(cmd)
            print(f"? Command conversion: {cmd} -> '{cmd_str}'")
            print(f"   Original type: {type(cmd)}")
            print(f"   Converted type: {type(cmd_str)}")

            # Test command array creation like in manager.py
            args = first_config.get("args", [])
            command_array = [str(cmd)] + args
            print(f"? Command array: {command_array}")
            print(f"   First element type: {type(command_array[0])}")
            return True
        else:
            print("? No configs to test")
            return False
    except Exception as e:
        print(f"? Command conversion test failed: {e}")
        return False


if __name__ == "__main__":
    print("?? Testing MCP Fixes\n")

    results = []
    results.append(test_command_enum())
    results.append(test_config_loading())
    results.append(test_command_conversion())

    print(f"\n?? Test Results: {sum(results)}/{len(results)} passed")

    if all(results):
        print("?? All tests passed! MCP fixes should work correctly.")
    else:
        print("? Some tests failed. Need to investigate further.")
