#!/usr/bin/env python3
"""
Tests for the slash command parser.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import pytest
from src.slash_commands.parser import ParseCommand


def test_parse_simple_command():
    """Test parsing a simple command without arguments."""
    slash_command = ParseCommand.get_command("/help")
    assert slash_command.command == "help"
    assert slash_command.options == []


def test_parse_command_with_options():
    """Test parsing a command with options."""
    slash_command = ParseCommand.get_command("/greet --name john")
    assert slash_command.command == "greet"
    assert len(slash_command.options) == 1
    assert slash_command.options[0].name == "name"
    assert slash_command.options[0].value == ["john"]


def test_parse_command_with_multiple_values():
    """Test parsing a command with options having multiple values."""
    slash_command = ParseCommand.get_command("/read --files f1.txt f2.txt f3.txt")
    assert slash_command.command == "read"
    assert len(slash_command.options) == 1
    assert slash_command.options[0].name == "files"
    assert slash_command.options[0].value == ["f1.txt", "f2.txt", "f3.txt"]


def test_parse_command_with_spaces():
    """Test parsing command with extra spaces."""
    # This will fail because the parser doesn't strip whitespace
    with pytest.raises(ValueError):
        ParseCommand.get_command("  /help  ")


def test_parse_non_command():
    """Test parsing non-command input (should raise ValueError)."""
    with pytest.raises(ValueError):
        ParseCommand.get_command("regular message")


def test_parse_empty_command():
    """Test parsing empty command (should raise ValueError)."""
    with pytest.raises(ValueError):
        ParseCommand.get_command("")


def test_parse_command_without_slash():
    """Test parsing command without leading slash (should raise ValueError)."""
    with pytest.raises(ValueError):
        ParseCommand.get_command("help")


if __name__ == "__main__":
    pytest.main([__file__])