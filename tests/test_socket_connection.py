"""
Quick test to verify socket connection works
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import sys
from pathlib import Path


print("Testing socket connection...")

from src.config import settings
from src.utils.socket_manager import SocketManager

# Test 1: Check paths
print(f"\nPaths:")
print(f"  BASE_DIR: {settings.BASE_DIR}")
print(f"  Expected log file: {settings.BASE_DIR / 'basic_logs' / 'error_log.txt'}")
print(f"  Log file exists: {(settings.BASE_DIR / 'basic_logs' / 'error_log.txt').exists()}")

# Test 2: Try to get socket connection
print(f"\nSocket settings:")
print(f"  ENABLE_SOCKET_LOGGING: {settings.ENABLE_SOCKET_LOGGING}")
print(f"  SOCKET_HOST: {settings.SOCKET_HOST}")
print(f"  SOCKET_PORT: {settings.SOCKET_PORT}")
print(f"  LOG_DISPLAY_MODE: {settings.LOG_DISPLAY_MODE}")

print(f"\nAttempting to get socket connection...")
manager = SocketManager()
socket_con = manager.get_socket_connection()

if socket_con:
    print(f"✅ Socket connection successful!")
    print(f"   Connection object: {socket_con}")

    # Test sending a message
    try:
        from src.ui.diagnostics.debug_helpers import debug_info
        debug_info("TEST • SOCKET", "Socket connection test successful", {"test_id": 1})
        print(f"✅ Test message sent successfully")
    except Exception as e:
        print(f"❌ Error sending test message: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"❌ Socket connection failed")
    print(f"   Check if error_transfer.py server is running")

print(f"\nTest complete!")

