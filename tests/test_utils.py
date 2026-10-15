"""
Test utilities for fixing import paths across all test files.

This module ensures that 'src' package is always importable regardless of:
- Running from PyCharm
- Running from terminal
- Running from project root
- Running from tests directory
"""
import sys
from pathlib import Path


def setup_project_path():
    """
    Add project root to sys.path to ensure 'src' imports work everywhere.

    This function:
    1. Finds the project root (directory containing 'src' folder)
    2. Adds it to sys.path if not already there
    3. Works from any subdirectory
    """
    # Get the current file's directory
    current_file = Path(__file__).resolve()

    # Navigate up to find project root (contains 'src' directory)
    current_dir = current_file.parent

    # Go up from tests/ to project root
    project_root = current_dir.parent

    # Verify this is the correct project root (should contain 'src' directory)
    src_dir = project_root / 'src'

    if not src_dir.exists():
        # If we're in a subdirectory of tests, go up one more level
        project_root = project_root.parent
        src_dir = project_root / 'src'

    if not src_dir.exists():
        raise RuntimeError(
            f"Cannot find 'src' directory. "
            f"Current location: {current_file}, "
            f"Tried: {project_root / 'src'}"
        )

    # Add project root to sys.path if not already there
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)

    return project_root


# Automatically setup path when this module is imported
PROJECT_ROOT = setup_project_path()


def get_project_root() -> Path:
    """Get the project root directory."""
    return PROJECT_ROOT


def get_src_dir() -> Path:
    """Get the src directory."""
    return PROJECT_ROOT / 'src'

