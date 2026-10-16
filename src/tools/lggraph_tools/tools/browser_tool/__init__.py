"""
Browser Tool Package

Re-exports from browser_tool_main.py for backwards compatibility.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Re-export from browser_tool_main.py for backwards compatibility
from src.tools.lggraph_tools.tools.browser_tool_main import (
    BrowserHandler,
    browser_use_tool,
)

# Also export Runner and Config for direct usage
from src.tools.lggraph_tools.tools.browser_tool.runner import Runner
from src.tools.lggraph_tools.tools.browser_tool.config import BrowserRequiredConfig

__all__ = ['BrowserHandler', 'browser_use_tool', 'Runner', 'BrowserRequiredConfig']

