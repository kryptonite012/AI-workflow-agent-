"""
Direct test of new_logger_write function
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import sys
from pathlib import Path


# Import the function
from src.utils.error_transfer import new_logger_write
import json

# Create a test message
test_message = json.dumps({
    "obj_type": "str",
    "data_type": "DebugMessage",
    "timestamp": "2025-12-17T10:00:00.000000",
    "data": {
        "heading": "DIRECT_TEST",
        "body": "Testing new_logger_write directly",
        "level": "INFO",
        "metadata": {"test": "direct"}
    }
})

print("Testing new_logger_write function directly...")
print(f"Input message: {test_message[:100]}...")

try:
    new_logger_write(test_message)
    print("✅ Function completed without exceptions")
except Exception as e:
    print(f"❌ Function failed with error: {e}")
    import traceback
    traceback.print_exc()

# Check if log files were created
import os
print("\nChecking for log files...")
for filename in os.listdir('.'):
    if filename.startswith('log_'):
        print(f"  Found: {filename}")
        with open(filename, 'r') as f:
            content = f.read()
            print(f"    Content: {content[:200]}")

if not any(f.startswith('log_') for f in os.listdir('.')):
    print("  No log files found")

print("\nTest complete!")

