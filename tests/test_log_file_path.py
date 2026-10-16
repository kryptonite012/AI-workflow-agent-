"""
Direct test to verify log file creation with absolute path
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import sys
from pathlib import Path


print("Testing log file creation with absolute path...")

from src.system_logging.on_time_registry import OnTimeRegistry
from src.system_logging.handlers.handler_base import TextHandler
from src.system_logging.dispatcher import Dispatcher
import json

# Register handler (idempotent)
registry = OnTimeRegistry()
handler = TextHandler()
if handler not in registry:
    registry.register(handler)
print("✓ Handler registered")

# Create test message
test_json = json.dumps({
    "LOG_TYPE": "OTHER",
    "LEVEL": "INFO",
    "MESSAGE": "Test message with absolute path",
    "TIME_STAMP": "2025-12-17T12:00:00",
    "METADATA": {"test": "absolute_path"}
})

# Dispatch
disp = Dispatcher()
disp.dispatch(test_json)
print("✓ Message dispatched")

# Check for log files in src/basic_logs
from src.config import settings
log_dir = settings.BASE_DIR / "basic_logs"
print(f"\nLooking for log files in: {log_dir}")

log_files = list(log_dir.glob("log_*.txt"))
if log_files:
    print(f"✓ Found {len(log_files)} log file(s):")
    for f in log_files:
        print(f"  - {f.name} ({f.stat().st_size} bytes)")
        with open(f, 'r') as file:
            content = file.read()
            print(f"    Content: {content[:150]}")
else:
    print("✗ No log files found!")
    print(f"  Directory exists: {log_dir.exists()}")
    print(f"  Directory contents: {list(log_dir.iterdir())}")

