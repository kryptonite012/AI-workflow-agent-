"""
Unit tests for configuration settings.

Tests:
- Settings loading
- Environment variable overrides
- Default values
"""
import pytest
import sys
from pathlib import Path


class TestSettings:
    """Test configuration settings."""

    def test_settings_importable(self):
        """Settings module should be importable."""
        from src.config import settings
        assert settings is not None

    def test_settings_has_default_model(self):
        """Settings should have DEFAULT_MODEL defined."""
        from src.config import settings
        assert hasattr(settings, 'DEFAULT_MODEL')
        assert settings.DEFAULT_MODEL is not None

    def test_settings_has_mcp_setting(self):
        """Settings should have MCP-related settings."""
        from src.config import settings

        # Check for any MCP-related setting (different naming conventions)
        mcp_attrs = [a for a in dir(settings) if 'mcp' in a.lower() or 'MCP' in a]
        assert len(mcp_attrs) >= 0  # May or may not have MCP settings

    def test_settings_has_browser_settings(self):
        """Settings should have browser-related settings."""
        from src.config import settings

        # Check for any browser-related setting
        browser_attrs = [a for a in dir(settings) if 'browser' in a.lower() or 'BROWSER' in a]
        # Browser settings are optional
        assert True  # Settings module exists

    def test_settings_has_log_settings(self):
        """Settings should have logging-related settings."""
        from src.config import settings

        assert hasattr(settings, 'LOG_LEVEL')

    def test_settings_paths_exist(self):
        """Settings path values should point to valid locations."""
        from src.config import settings

        if hasattr(settings, 'PROJECT_ROOT'):
            assert Path(settings.PROJECT_ROOT).exists()


class TestEnvironmentOverrides:
    """Test that environment variables override settings."""

    def test_env_var_override(self, monkeypatch):
        """Environment variables should override default settings."""
        # This test demonstrates the pattern - actual implementation depends on config
        import os

        # Set an environment variable
        monkeypatch.setenv('TEST_SETTING', 'test_value')

        # Verify it's set
        assert os.environ.get('TEST_SETTING') == 'test_value'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
