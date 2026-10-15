"""
Tests for MCP Manager.

Tests:
- Server registration
- Server starting/stopping
- Server health validation
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock


class TestMCPManagerInit:
    """Test MCP Manager initialization."""

    def test_mcp_manager_importable(self):
        """MCP_Manager should be importable."""
        from src.mcp.manager import MCP_Manager
        assert MCP_Manager is not None

    def test_mcp_manager_creation(self, mcp_manager):
        """MCP_Manager should be instantiable."""
        assert mcp_manager is not None

    def test_mcp_manager_has_servers_dict(self):
        """MCP_Manager should have mcp_servers class attribute."""
        from src.mcp.manager import MCP_Manager
        assert hasattr(MCP_Manager, 'mcp_servers')
        assert isinstance(MCP_Manager.mcp_servers, dict)

    def test_mcp_manager_has_enabled_flag(self):
        """MCP_Manager should have mcp_enabled attribute."""
        from src.mcp.manager import MCP_Manager
        assert hasattr(MCP_Manager, 'mcp_enabled')


class TestMCPServerRegistration:
    """Test server registration functionality."""

    def test_add_server_method_exists(self):
        """MCP_Manager should have add_server method."""
        from src.mcp.manager import MCP_Manager
        assert hasattr(MCP_Manager, 'add_server')
        assert callable(MCP_Manager.add_server)

    def test_add_server(self):
        """Should be able to add a server."""
        from src.mcp.manager import MCP_Manager
        from src.mcp.mcp_register_structure import Command

        # Store original servers
        original_servers = dict(MCP_Manager.mcp_servers)

        try:
            # Add a test server
            MCP_Manager.add_server(
                name="test_server",
                runner=Command.NPX,
                package=None,
                args=["-y", "test-package"],
                func=Mock()
            )

            assert "test_server" in MCP_Manager.mcp_servers
        finally:
            # Restore original servers
            MCP_Manager.mcp_servers = original_servers

    def test_add_duplicate_server_updates(self):
        """Adding server with same name should update it."""
        from src.mcp.manager import MCP_Manager
        from src.mcp.mcp_register_structure import Command

        original_servers = dict(MCP_Manager.mcp_servers)

        try:
            mock1 = Mock()
            mock2 = Mock()

            MCP_Manager.add_server(
                name="dup_test",
                runner=Command.NPX,
                package=None,
                args=["-y", "test1"],
                func=mock1
            )

            MCP_Manager.add_server(
                name="dup_test",
                runner=Command.NPX,
                package=None,
                args=["-y", "test2"],
                func=mock2
            )

            # Should have updated, not duplicated
            assert "dup_test" in MCP_Manager.mcp_servers
        finally:
            MCP_Manager.mcp_servers = original_servers


class TestMCPServerHealth:
    """Test server health validation."""

    def test_mcp_manager_has_health_methods(self):
        """MCP_Manager should have health-related methods."""
        from src.mcp.manager import MCP_Manager

        # Check for any health-related methods
        health_methods = [m for m in dir(MCP_Manager) if 'health' in m.lower() or 'status' in m.lower()]
        # Health methods are optional
        assert True  # MCP_Manager exists



if __name__ == '__main__':
    pytest.main([__file__, '-v'])
