"""
Test to check if handlers are registered
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import sys
from pathlib import Path


print("Checking handler registration...")

# Register handlers like error_transfer.py does
from src.system_logging.on_time_registry import OnTimeRegistry
from src.system_logging.handlers.handler_base import TextHandler

registry = OnTimeRegistry()
print(f"Registry before registration: {len(registry._handlers)} handlers")

try:
    registry.register(TextHandler())
    print(f"✅ Handler registered successfully")
except Exception as e:
    print(f"❌ Handler registration failed: {e}")
    import traceback
    traceback.print_exc()

print(f"Registry after registration: {len(registry._handlers)} handlers")

# Try to get all handlers
try:
    handlers = registry.get_all_handlers()
    print(f"✅ Got {len(handlers)} handlers from registry")
    for h in handlers:
        print(f"  - {h.name}")
except Exception as e:
    print(f"❌ Failed to get handlers: {e}")

# Now test dispatch
from src.system_logging.dispatcher import Dispatcher
import json

test_json = json.dumps({
    "LOG_TYPE": "OTHER",
    "LEVEL": "INFO",
    "MESSAGE": "Test message",
    "TIME_STAMP": "2025-12-17T10:00:00",
    "METADATA": {}
})

print(f"\nTesting dispatch...")
try:
    disp = Dispatcher()
    disp.dispatch(test_json)
    print(f"✅ Dispatch completed")
except Exception as e:
    print(f"❌ Dispatch failed: {e}")
    import traceback
    traceback.print_exc()

# Check for log files
import os
print(f"\nChecking for log files in: {os.getcwd()}")
log_files = [f for f in os.listdir('.') if f.startswith('log_')]
if log_files:
    print(f"✅ Found {len(log_files)} log files:")
    for f in log_files:
        print(f"  - {f}")
        with open(f, 'r') as file:
            content = file.read()
            print(f"    Content: {content[:100]}")
else:
    print("❌ No log files found")

