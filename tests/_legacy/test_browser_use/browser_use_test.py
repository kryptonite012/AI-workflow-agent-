"""
Simple test script to verify that the browser use tool is working correctly.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def test_browser_use():
    """Test browser tool with simple navigation."""
    try:
        from src.tools.lggraph_tools.tools.browser_tool import browser_use_tool

        # Test with a simple query
        result = browser_use_tool(
            query="you have play song called the night we met on youtube keep alive and log to the true",
            head_less_mode=False,
            log=True,
            keep_alive=True
        )
        print(f"Result: {result}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_browser_use()
    sys.exit(0 if success else 1)

