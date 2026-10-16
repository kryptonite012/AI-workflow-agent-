"""Unit tests for BrowserRequiredConfig."""
import pytest
from pathlib import Path


class TestBrowserRequiredConfig:
    """Test BrowserRequiredConfig dataclass."""

    def test_minimal_config_creation(self, tmp_path):
        """Config with only required fields should work."""
        from src.tools.lggraph_tools.tools.browser_tool.config import BrowserRequiredConfig

        config = BrowserRequiredConfig(
            query="test",
            file_path=tmp_path / "result.json"
        )

        assert config.query == "test"
        assert config.file_path == tmp_path / "result.json"

    def test_config_has_defaults(self, minimal_config):
        """Config should have sensible defaults."""
        assert minimal_config.headless == False
        assert minimal_config.keep_alive == True
        assert minimal_config.log == True
        assert minimal_config.max_failures == 5
        assert minimal_config.max_steps == 500

    def test_config_is_mutable(self, minimal_config):
        """Config is currently mutable (dataclass is not frozen)."""
        minimal_config.query = "new query"
        assert minimal_config.query == "new query"

    def test_config_accepts_all_options(self, full_config):
        """Config should accept all optional parameters."""
        assert full_config.query == "Go to example.com"
        assert full_config.headless == True
        assert full_config.keep_alive == False
        assert full_config.max_failures == 3
        assert full_config.max_steps == 100
        assert full_config.vision_detail_level == 'medium'
        assert full_config.record_video == True

    def test_config_validates_paths(self, tmp_path):
        """Config should accept Path objects."""
        from src.tools.lggraph_tools.tools.browser_tool.config import BrowserRequiredConfig

        result_file = tmp_path / "result.json"
        video_dir = tmp_path / "videos"
        user_data_dir = tmp_path / "profile"

        config = BrowserRequiredConfig(
            query="test",
            file_path=result_file,
            video_dir=video_dir,
            user_data_dir=user_data_dir
        )

        assert isinstance(config.file_path, Path)
        assert isinstance(config.video_dir, Path)
        assert isinstance(config.user_data_dir, Path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
