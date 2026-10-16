# 🚨 LEGACY TESTS - DO NOT USE

These tests use OLD API that no longer exists.

## ❌ Deprecated API

| Old API | Status | Replacement |
|---------|--------|-------------|
| `browser_use_tool()` function | ❌ REMOVED | Use `Runner` + `BrowserRequiredConfig` |
| `BrowserHandler` class | ❌ REMOVED | Use `Runner` class |
| `BrowserUseCompatibleLLM` | ✅ EXISTS | In `browser_subprocess_runner.py` (will be moved) |
| `save_custom_sessions()` | ❌ STANDALONE | Now in `SessionManager` class |
| `load_custom_sessions()` | ❌ STANDALONE | Now in `SessionManager` class |

## 📝 Migration Guide

### Old Way (BROKEN):
```python
from src.tools.lggraph_tools.tools.browser_tool import browser_use_tool

result = browser_use_tool(
    query="Go to example.com",
    head_less_mode=True,
    log=True,
    keep_alive=False
)
```

### New Way (WORKING):
```python
from src.tools.lggraph_tools.tools.browser_tool.runner import Runner
from src.tools.lggraph_tools.tools.browser_tool.config import BrowserRequiredConfig
from pathlib import Path

config = BrowserRequiredConfig(
    query="Go to example.com",
    file_path=Path("result.json"),
    headless=True,
    keep_alive=False,
    log=True
)

runner = Runner(config)
result = await runner.run()
```

## 🗑️ Files in This Directory

- `browser_use_test.py` - Used `browser_use_tool()`
- `test_browser_comprehensive.py` - Used `BrowserHandler`, `BrowserUseCompatibleLLM`
- `test_session_resurrection.py` - Used standalone session functions

**These tests are BROKEN and should NOT be run!**

Use the new tests in `/tests/browser_tool/` instead.
