from typing import Any

from src.mcp.manager import MCP_Manager


def file_system_tool(**kwargs) -> str | dict | list[dict[str, Any]]:
    """
    Universal MCP filesystem tool that handles all MCP operations dynamically.

    This function automatically detects which MCP tool to call based on the
    tool name stored in the ToolAssign instance, then routes parameters accordingly.

    :param kwargs: Dynamic parameters that vary by MCP tool
    :return: Result from the specific MCP tool operation
    """

    try:
        # Safe debug system_logging
        from src.ui.diagnostics.debug_helpers import debug_info

        debug_info(
            heading="MCP_FILESYSTEM • CALL",
            body="Calling MCP server",
            metadata={"kwargs_preview": str(kwargs)[:100], "kwargs_count": len(kwargs)},
        )

        tool_name = kwargs.pop(
            "tool_name", "unknown tool"
        )  # Extract tool name from kwargs
        arguments = kwargs
        response = MCP_Manager.call_mcp_server("filesystem", tool_name, arguments)

        debug_info(
            heading="MCP_FILESYSTEM • PARAMETERS",
            body=f"Tool: {tool_name}",
            metadata={"tool_name": tool_name, "arguments": arguments},
        )

        if response is None:
            return "Error: No response from MCP server"

        if response.get("success"):
            # Extract the actual content from the structured response
            data = response.get("data")
            debug_info(
                heading="MCP_FILESYSTEM • SUCCESS",
                body="Response received from MCP server",
                metadata={
                    "data_type": type(data).__name__,
                    "has_content": "content" in data
                    if isinstance(data, dict)
                    else False,
                },
            )
            return (
                data["content"]
                if isinstance(data, dict) and "content" in data
                else "No content returned"
            )
        else:
            # Handle error response
            error_msg = response.get("error", "Unknown error occurred")
            from src.utils.debug_helpers import debug_error

            debug_error(
                heading="MCP_FILESYSTEM • ERROR",
                body=f"Error from MCP server: {error_msg}",
                metadata={"error_message": error_msg, "response": response},
            )
            return response

    except Exception as e:
        return f"Error: Exception in filesystem tool: {str(e)}"
