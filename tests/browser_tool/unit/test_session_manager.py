"""Unit tests for SessionManager class."""
import pytest
import asyncio
from pathlib import Path


class TestSessionManager:
    """Test SessionManager functionality."""

    def test_session_manager_creation(self, tmp_path):
        """SessionManager should be creatable with profile_dir."""
        from src.tools.lggraph_tools.tools.browser_tool.utils.session_manager import SessionManager

        manager = SessionManager(profile_dir=tmp_path)
        assert manager is not None
        assert manager._profile_dir == tmp_path

    def test_session_manager_default_path(self):
        """SessionManager should have default profile path."""
        from src.tools.lggraph_tools.tools.browser_tool.utils.session_manager import SessionManager

        manager = SessionManager()
        assert manager._profile_dir is not None
        assert isinstance(manager._profile_dir, Path)

    # TODO: Add tests for attach(), save(), load() methods
    # These require mocking Browser instance


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
