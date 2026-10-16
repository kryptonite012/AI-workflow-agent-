from src.config import settings
from src.tools.lggraph_tools.tools.mcp_integrated_tools import filesystem


class FileSystemWrapper:
    """
    Wrapper class for filesystem operations using MCP server.
    Follows the same pattern as GoogleSearchToolWrapper and TranslateToolWrapper.
    """

    def __init__(self, **kwargs):
        from src.tools.lggraph_tools.tool_response_manager import ToolResponseManager

        self.file_path = kwargs.get("path", None)
        """
        Initialize the FileSystemWrapper with a file path and action.

        :param file_path: The path to the file to operate on.
        :param action: The action to perform (read_file, write_file, delete_file).
        """

        # Call the filesystem tool (now returns structured response)
        result = filesystem.file_system_tool(**kwargs)

        # Safe debug system_logging
        from src.ui.diagnostics.debug_helpers import debug_info

        debug_info(
            heading="MCP_WRAPPER • FILESYSTEM",
            body="MCP server result received",
            metadata={
                "result_preview": str(result)[:100],
                "result_type": type(result).__name__,
            },
        )

        action = kwargs.get("tool_name")  # This should match the action being performed
        debug_info(
            heading="MCP_WRAPPER • ACTION",
            body=f"Action performed: {action}",
            metadata={"action": action, "kwargs_count": len(kwargs)},
        )

        # Handle the result and create appropriate AI message
        if result and not str(result).startswith("Error:"):
            # Success - create clean response
            if action == "read_file":
                content = (
                    f"📄 **File Content ({self.file_path}):**\n\n{result[0]['content']}"
                )
            elif action == "write_file":
                content = f"✅ **File Written Successfully:** {self.file_path}"
            elif action == "delete_file":
                content = f"🗑️ **File Deleted Successfully:** {self.file_path}"
            else:
                content = f"✅ **{action} completed for:** {self.file_path}\n\nResult: {result}"

            ToolResponseManager().set_response([settings.AIMessage(content=content)])
        else:
            # Error handling with clean error message
            error_msg = result if result else "Unknown error occurred"

            # Clean up error message for user
            if error_msg.startswith("Error: "):
                error_msg = error_msg[7:]  # Remove "Error: " prefix

            content = f"❌ **Filesystem Operation Failed**\n\n**Action:** {action}\n**File:** {self.file_path}\n**Error:** {error_msg}"

            ToolResponseManager().set_response([settings.AIMessage(content=content)])
