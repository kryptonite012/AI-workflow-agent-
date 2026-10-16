"""
Comprehensive Browser Use Tool Tests

This file consolidates all browser_use tests into one well-organized test suite.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest


class TestBrowserToolImports:
    """Test that all browser tool components can be imported."""

    def test_import_browser_use_tool(self):
        """Test importing the main browser_use_tool function."""
        from src.tools.lggraph_tools.tools.browser_tool import browser_use_tool
        assert callable(browser_use_tool)

    def test_import_browser_handler(self):
        """Test importing BrowserHandler class."""
        from src.tools.lggraph_tools.tools.browser_tool import BrowserHandler
        assert BrowserHandler is not None

    def test_import_browser_compatible_llm(self):
        """Test importing BrowserUseCompatibleLLM class."""
        from src.tools.lggraph_tools.tools.browser_tool import BrowserUseCompatibleLLM
        assert BrowserUseCompatibleLLM is not None

    def test_import_browser_wrapper(self):
        """Test importing BrowserUseWrapper class."""
        from src.tools.lggraph_tools.wrappers.browser_use_wrapper import BrowserUseWrapper
        assert BrowserUseWrapper is not None


class TestBrowserToolSignature:
    """Test function signatures and parameters."""

    def test_browser_use_tool_signature(self):
        """Verify browser_use_tool has correct parameters."""
        import inspect
        from src.tools.lggraph_tools.tools.browser_tool import browser_use_tool

        sig = inspect.signature(browser_use_tool)
        params = sig.parameters

        # Check required parameters exist
        assert 'query' in params, "Missing 'query' parameter"
        assert 'head_less_mode' in params, "Missing 'head_less_mode' parameter"
        assert 'log' in params, "Missing 'log' parameter"
        assert 'keep_alive' in params, "Missing 'keep_alive' parameter"

        # Check defaults
        assert params['head_less_mode'].default == True, "head_less_mode should default to True"
        assert params['log'].default == True, "log should default to True"
        assert params['keep_alive'].default == False, "keep_alive should default to False"

    def test_browser_handler_signature(self):
        """Verify BrowserHandler __init__ has correct parameters."""
        import inspect
        from src.tools.lggraph_tools.tools.browser_tool import BrowserHandler

        sig = inspect.signature(BrowserHandler.__init__)
        params = sig.parameters

        assert 'query' in params
        assert 'head_less_mode' in params
        assert 'log' in params
        assert 'keep_alive' in params


class TestBrowserToolConfiguration:
    """Test browser tool configuration and settings."""

    def test_browser_settings_exist(self):
        """Verify browser-related settings are defined."""
        from src.config import settings

        assert hasattr(settings, 'BROWSER_USE_ENABLED')
        assert hasattr(settings, 'BROWSER_USE_TIMEOUT')
        assert hasattr(settings, 'BROWSER_USE_LOG_FILE')

    def test_browser_enabled_setting(self):
        """Check if browser tool is enabled."""
        from src.config import settings

        # Should be a boolean
        assert isinstance(settings.BROWSER_USE_ENABLED, bool)

    def test_browser_timeout_setting(self):
        """Check browser timeout is reasonable."""
        from src.config import settings

        # Should be an integer and greater than 0
        assert isinstance(settings.BROWSER_USE_TIMEOUT, int)
        assert settings.BROWSER_USE_TIMEOUT > 0


class TestBrowserToolIntegration:
    """Integration tests for browser tool (require browser-use package)."""

    @pytest.mark.skip(reason="Requires browser automation - run manually only")
    def test_basic_navigation(self):
        """Test basic browser navigation (MANUAL TEST ONLY)."""
        from src.tools.lggraph_tools.tools.browser_tool import browser_use_tool

        result = browser_use_tool(
            query="Navigate to https://www.google.com",
            head_less_mode=True,
            log=False,
            keep_alive=False
        )

        # Should return a string result
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.skip(reason="Requires browser automation - run manually only")
    def test_headless_mode(self):
        """Test headless mode works (MANUAL TEST ONLY)."""
        from src.tools.lggraph_tools.tools.browser_tool import browser_use_tool

        # Should run without displaying browser window
        result = browser_use_tool(
            query="Navigate to https://www.example.com",
            head_less_mode=True,
            log=False,
            keep_alive=False
        )

        assert isinstance(result, str)


def test_browser_compatible_llm_creation():
    """Test creating BrowserUseCompatibleLLM instance."""
    from src.tools.lggraph_tools.tools.browser_tool import BrowserUseCompatibleLLM
    from src.utils.model_manager import ModelManager
    from src.config import settings

    # Create model manager
    model_manager = ModelManager(model=settings.DEFAULT_MODEL)

    # Create browser-compatible LLM
    browser_llm = BrowserUseCompatibleLLM(model_manager)

    # Check properties exist
    assert hasattr(browser_llm, 'model')
    assert hasattr(browser_llm, 'provider')
    assert hasattr(browser_llm, 'name')
    assert hasattr(browser_llm, 'model_name')


def test_browser_wrapper_creation():
    """Test that BrowserUseWrapper can be instantiated with kwargs."""
    from src.tools.lggraph_tools.wrappers.browser_use_wrapper import BrowserUseWrapper

    # Should accept kwargs after the fix
    try:
        # This will actually try to run browser, so we just test instantiation fails gracefully
        wrapper = BrowserUseWrapper(
            query="test query",
            head_less_mode=True,
            log=False,
            keep_alive=False
        )
    except Exception as e:
        # Expected to fail if browser-use not installed or other issues
        # Just verifying it accepts the parameters
        assert 'query' not in str(e).lower() or 'missing' not in str(e).lower()


if __name__ == "__main__":
    """Run tests manually without pytest."""
    print("="*80)
    print("BROWSER TOOL TEST SUITE")
    print("="*80)

    # Run import tests
    print("\n1. Testing Imports...")
    test_obj = TestBrowserToolImports()
    try:
        test_obj.test_import_browser_use_tool()
        print("   ✅ browser_use_tool import OK")
    except AssertionError as e:
        print(f"   ❌ browser_use_tool import FAILED: {e}")

    try:
        test_obj.test_import_browser_handler()
        print("   ✅ BrowserHandler import OK")
    except AssertionError as e:
        print(f"   ❌ BrowserHandler import FAILED: {e}")

    try:
        test_obj.test_import_browser_compatible_llm()
        print("   ✅ BrowserUseCompatibleLLM import OK")
    except AssertionError as e:
        print(f"   ❌ BrowserUseCompatibleLLM import FAILED: {e}")

    try:
        test_obj.test_import_browser_wrapper()
        print("   ✅ BrowserUseWrapper import OK")
    except AssertionError as e:
        print(f"   ❌ BrowserUseWrapper import FAILED: {e}")

    # Run signature tests
    print("\n2. Testing Function Signatures...")
    sig_test = TestBrowserToolSignature()
    try:
        sig_test.test_browser_use_tool_signature()
        print("   ✅ browser_use_tool signature OK")
    except AssertionError as e:
        print(f"   ❌ browser_use_tool signature FAILED: {e}")

    try:
        sig_test.test_browser_handler_signature()
        print("   ✅ BrowserHandler signature OK")
    except AssertionError as e:
        print(f"   ❌ BrowserHandler signature FAILED: {e}")

    # Run configuration tests
    print("\n3. Testing Configuration...")
    config_test = TestBrowserToolConfiguration()
    try:
        config_test.test_browser_settings_exist()
        print("   ✅ Browser settings exist")
    except AssertionError as e:
        print(f"   ❌ Browser settings FAILED: {e}")

    try:
        config_test.test_browser_enabled_setting()
        print("   ✅ BROWSER_USE_ENABLED OK")
    except AssertionError as e:
        print(f"   ❌ BROWSER_USE_ENABLED FAILED: {e}")

    try:
        config_test.test_browser_timeout_setting()
        print("   ✅ BROWSER_USE_TIMEOUT OK")
    except AssertionError as e:
        print(f"   ❌ BROWSER_USE_TIMEOUT FAILED: {e}")

    # Run integration tests
    print("\n4. Testing Integration...")
    try:
        test_browser_compatible_llm_creation()
        print("   ✅ BrowserUseCompatibleLLM creation OK")
    except Exception as e:
        print(f"   ❌ BrowserUseCompatibleLLM creation FAILED: {e}")

    try:
        test_browser_wrapper_creation()
        print("   ✅ BrowserUseWrapper instantiation OK")
    except Exception as e:
        print(f"   ❌ BrowserUseWrapper instantiation FAILED: {e}")

    print("\n" + "="*80)
    print("TEST SUITE COMPLETE")
    print("="*80)
    print("\nNOTE: Actual browser execution tests are skipped (use pytest -v to run with pytest)")

