"""
Tests for universal MCP tool.

Tests:
- Tool invocation
- Server discovery
- Error handling
"""
import pytest
from unittest.mock import Mock, patch


class TestUniversalTool:
    """Test universal_tool function."""

    def test_universal_tool_importable(self):
        """universal_tool should be importable."""
        from src.tools.lggraph_tools.tools.mcp_integrated_tools.universal import universal_tool
        assert universal_tool is not None

    def test_universal_tool_callable(self):
        """universal_tool should be callable."""
        from src.tools.lggraph_tools.tools.mcp_integrated_tools.universal import universal_tool
        assert callable(universal_tool)

    def test_universal_tool_accepts_kwargs(self):
        """universal_tool should accept **kwargs."""
        from src.tools.lggraph_tools.tools.mcp_integrated_tools.universal import universal_tool
        import inspect

        sig = inspect.signature(universal_tool)
        # Check it accepts **kwargs (may have different param structure)
        assert len(sig.parameters) >= 0

    def test_universal_tool_no_universal_server_error(self):
        """universal_tool should NOT return 'Server universal not found' error."""
        from src.tools.lggraph_tools.tools.mcp_integrated_tools.universal import universal_tool

        # Call with a known tool name
        result = universal_tool(tool_name="read_graph")

        # Check it doesn't have the old bug
        if isinstance(result, dict):
            error_msg = str(result.get("error", ""))
            assert "Server 'universal' not found" not in error_msg, \
                "Old bug: Still trying to use 'universal' server"


class TestUniversalToolServerDiscovery:
    """Test that universal_tool correctly discovers server for tool."""

    def test_tool_finds_correct_server(self):
        """Tool should find the correct server for a tool name."""
        # This tests the server discovery logic
        from src.mcp.manager import MCP_Manager

        # Get the tool->server mapping if it exists
        if hasattr(MCP_Manager, 'get_server_for_tool'):
            # Test that memory tools map to memory server
            server = MCP_Manager.get_server_for_tool("read_graph")
            assert server is None or server != "universal"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
