"""
Universal MCP Wrapper

This module provides a universal wrapper for Modular Control Platform (MCP) servers.
It allows seamless integration with any MCP server, regardless of the specific tools or APIs provided.
By using this wrapper, developers can avoid creating and maintaining separate wrappers for each unique MCP server implementation.
"""
import json
from typing import Any


class UniversalMCPWrapper:
    """
    Universal wrapper for MCP servers.
    This class allows interaction with any MCP server without needing to create specific wrappers for each server.
    """

    def __init__(self, **kwargs):
        from src.tools.lggraph_tools.tool_response_manager import ToolResponseManager
        from src.tools.lggraph_tools.tools.mcp_integrated_tools.universal import (
            universal_tool,
        )
        from src.config import settings

        self.server_url = kwargs.get("server_url", None)
        self.action = kwargs.get("tool_name", None)
        self.params = kwargs.get("params", {})

        # Call the MCP server with the provided parameters
        result = universal_tool(**kwargs)

        # --- START OF INTELLIGENT UNWRAPPING LOGIC ---

        final_content = result  # Default to the original result

        # Check if the result is a list containing a dictionary with a 'text' key
        if isinstance(result, list) and result and isinstance(result[0], dict) and "text" in result[0]:
            try:
                final_content = result[0].get("text", str(result))
            except (IndexError, KeyError, TypeError):
                final_content = str(result)
        # Check if the result is the dictionary from a resolved URI
        elif isinstance(result, dict) and "contents" in result and isinstance(result["contents"], list):
            try:
                final_content = result["contents"][0].get("text", str(result))
            except (IndexError, KeyError, TypeError):
                final_content = json.dumps(result, indent=2)
        # If the result is any other dictionary, pretty-print it
        elif isinstance(result, dict):
            # Avoid formatting our own error messages
            if not ("success" in result and result.get("success") is False):
                final_content = json.dumps(result, indent=2)

        # --- END OF LOGIC ---

        # Safe debug system_logging
        from src.ui.diagnostics.debug_helpers import debug_info

        debug_info(
            heading="MCP_WRAPPER • UNIVERSAL",
            body="MCP server result received",
            metadata={
                "result_preview": str(result),
                "result_type": type(result).__name__,
            },
        )

        # Handle the result and create appropriate AI message
        if result and not str(result).startswith("Error:")  :
            content = f"✅ **Action '{self.action}' completed successfully.**\n\nResult: {final_content}"
            ToolResponseManager().set_response([settings.AIMessage(content=content)])
        else:
            error_msg = result if result else "Unknown error occurred"
            ToolResponseManager().set_response(
                [settings.AIMessage(content=f"❌ **Error:** {error_msg}")]
            )
