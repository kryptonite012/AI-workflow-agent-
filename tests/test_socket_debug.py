"""
Test to see what's happening with socket connection
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import sys
from pathlib import Path


print("=== SOCKET CONNECTION DEBUG ===\n")

# Import settings first
from src.config import settings
print(f"1. ENABLE_SOCKET_LOGGING: {settings.ENABLE_SOCKET_LOGGING}")
print(f"2. SOCKET_HOST: {settings.SOCKET_HOST}")
print(f"3. SOCKET_PORT: {settings.SOCKET_PORT}")
print(f"4. LOG_DISPLAY_MODE: {settings.LOG_DISPLAY_MODE}")

# Check if socket_con already exists
print(f"\n5. settings.socket_con before SocketManager: {settings.socket_con}")

# Now try to get connection
from src.utils.socket_manager import SocketManager

manager = SocketManager()
print(f"\n6. SocketManager._socket_con: {manager._socket_con}")
print(f"7. SocketManager._log_server_process: {manager._log_server_process}")

# Check if there's a stale server.lock file
from src.config import settings as s
lock_file = s.BASE_DIR / "basic_logs" / "server.lock"
print(f"\n8. Lock file exists: {lock_file.exists()}")
if lock_file.exists():
    try:
        with open(lock_file, 'r') as f:
            pid = f.read()
            print(f"   Lock file PID: {pid}")
    except Exception as e:
        print(f"   Error reading lock file: {e}")

# Try to get connection
print(f"\n9. Attempting to get socket connection...")
socket_con = manager.get_socket_connection()
print(f"10. Result: {socket_con}")

if socket_con:
    print(f"11. Socket connection type: {type(socket_con)}")
    print(f"12. Has _is_connected: {hasattr(socket_con, '_is_connected')}")
    if hasattr(socket_con, '_is_connected'):
        print(f"13. _is_connected(): {socket_con._is_connected()}")

# Check if server process started
print(f"\n14. SocketManager._log_server_process after: {manager._log_server_process}")
if manager._log_server_process:
    print(f"15. Process PID: {manager._log_server_process.pid}")
    print(f"16. Process poll: {manager._log_server_process.poll()}")

# Check port
import socket as sock
print(f"\n17. Testing port 5390...")
test_sock = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
test_sock.settimeout(0.5)
try:
    test_sock.connect(('localhost', 5390))
    print(f"    Port 5390: OPEN and accepting connections")
    test_sock.close()
except Exception as e:
    print(f"    Port 5390: CLOSED ({e})")

print(f"\n=== DEBUG COMPLETE ===")

