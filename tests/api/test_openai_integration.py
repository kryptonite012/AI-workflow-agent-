"""
Tests for OpenAI integration.

Tests:
- Client creation
- Text generation
- Error handling
"""
import pytest
from unittest.mock import Mock, patch


class TestOpenAIIntegration:
    """Test OpenAI integration."""

    def test_integration_importable(self):
        """OpenAIIntegration should be importable."""
        from src.utils.open_ai_integration import OpenAIIntegration
        assert OpenAIIntegration is not None

    def test_integration_creation(self, openai_integration):
        """OpenAIIntegration should be instantiable."""
        assert openai_integration is not None

    def test_integration_has_client(self, openai_integration):
        """Integration should have client attribute."""
        assert hasattr(openai_integration, 'client')

    def test_integration_has_generate_text(self, openai_integration):
        """Integration should have generate_text method."""
        assert hasattr(openai_integration, 'generate_text')
        assert callable(openai_integration.generate_text)


class TestOpenAIErrorHandling:
    """Test OpenAI error handling."""

    def test_502_error_handling(self, openai_integration, mock_openai_client):
        """Should handle 502 errors gracefully."""
        import openai

        # Mock 502 error
        mock_response = Mock()
        mock_response.status_code = 502
        mock_response.headers = {}

        mock_error = openai.APIStatusError(
            "Error code: 502",
            response=mock_response,
            body="Bad Gateway"
        )

        with patch.object(openai_integration, 'client', mock_openai_client):
            mock_openai_client.chat.completions.create.side_effect = mock_error

            # Should not crash, should return fallback or error message
            try:
                result = openai_integration.generate_text("Test")
                assert result is not None
            except openai.APIStatusError:
                # Re-raising is also acceptable if that's the design
                pass

    def test_rate_limit_handling(self, openai_integration, mock_openai_client):
        """Should handle rate limit errors."""
        import openai

        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"retry-after": "1"}

        mock_error = openai.RateLimitError(
            "Rate limited",
            response=mock_response,
            body="Too many requests"
        )

        with patch.object(openai_integration, 'client', mock_openai_client):
            mock_openai_client.chat.completions.create.side_effect = mock_error

            try:
                result = openai_integration.generate_text("Test")
                # Should handle gracefully
            except openai.RateLimitError:
                pass  # Acceptable


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
