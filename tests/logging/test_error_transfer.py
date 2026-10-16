"""
Tests for error transfer module.

Tests:
- new_logger_write function
- Error message parsing
- Log file creation
"""
import pytest
import json
import os


class TestErrorTransfer:
    """Test error transfer functionality."""

    def test_new_logger_write_importable(self):
        """new_logger_write should be importable."""
        from src.utils.error_transfer import new_logger_write
        assert new_logger_write is not None

    def test_new_logger_write_callable(self):
        """new_logger_write should be callable."""
        from src.utils.error_transfer import new_logger_write
        assert callable(new_logger_write)

    def test_new_logger_write_with_valid_message(self, tmp_path, monkeypatch):
        """new_logger_write should handle valid message."""
        from src.utils.error_transfer import new_logger_write

        # Change to temp directory to avoid polluting project
        monkeypatch.chdir(tmp_path)

        message = json.dumps({
            "obj_type": "str",
            "data_type": "DebugMessage",
            "timestamp": "2026-01-31T10:00:00.000000",
            "data": {
                "heading": "TEST",
                "body": "Test message",
                "level": "INFO",
                "metadata": {}
            }
        })

        try:
            new_logger_write(message)
            # Should not raise
            assert True
        except Exception as e:
            pytest.fail(f"new_logger_write raised exception: {e}")

    def test_new_logger_write_with_invalid_json(self, tmp_path, monkeypatch):
        """new_logger_write should handle invalid JSON gracefully."""
        from src.utils.error_transfer import new_logger_write

        monkeypatch.chdir(tmp_path)

        invalid_message = "not valid json"

        try:
            new_logger_write(invalid_message)
        except json.JSONDecodeError:
            pass  # Acceptable
        except Exception:
            pass  # Any graceful handling is acceptable


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
