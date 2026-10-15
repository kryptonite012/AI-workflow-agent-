import os
import socket
import subprocess
import sys
import time
import pathlib

# Handle imports - works both as module and standalone script
try:
    # Try relative import first (when run as module)
    from .error_transfer import SocketCon
except ImportError:
    # If relative import fails, try absolute import (when run as script)
    try:
        from error_transfer import SocketCon
    except ImportError:
        # Last resort: add current directory to path and import
        sys.path.append(pathlib.Path(pathlib.Path(__file__).resolve()).parent)
        from error_transfer import SocketCon

# Import settings - handle case where it might not be available
from src.config import settings
import pathlib

# Structured debug protocol imports (lazy fallback if unavailable)
try:
    from src.ui.diagnostics.debug_message_protocol import DebugMessageSender, LogLevel
except ImportError:  # Minimal fallbacks so legacy still works

    class DebugMessageSender:  # type: ignore
        def __init__(self, socket_connection=None):
            self.socket_connection = socket_connection

        def send_plain_text(self, text: str):
            if self.socket_connection and hasattr(self.socket_connection, "send_error"):
                self.socket_connection.send_error(text)
            else:
                print(text)

        # Unified interface expected below
        def send_debug_message(self, heading, body, level, metadata=None):
            self.send_plain_text(f"[{level}] {heading} - {body} :: {metadata or {}}")

    class LogLevel:  # type: ignore
        INFO = "INFO"
        WARNING = "WARNING"
        ERROR = "ERROR"
        CRITICAL = "CRITICAL"


class SocketManager:
    instance = None
    _socket_con = None
    _log_server_process = None
    _cleanup_in_progress = False  # Flag to prevent new connections during cleanup
    # Exposed safe wrapper placeholder (assigned after class definition)

    def __new__(cls):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    @staticmethod
    def get_socket_con():
        """Get socket connection only when needed"""
        return (
            SocketManager().get_socket_connection()
            if settings.ENABLE_SOCKET_LOGGING
            else None
        )

    def _build_debug_sender(self):
        """Internal helper to always return a DebugMessageSender bound to current connection"""
        return DebugMessageSender(self._socket_con)

    def start_log_server(self):
        """Start the log server as a subprocess"""
        if self._log_server_process is not None:
            # Check if process is still running
            if self._log_server_process.poll() is None:
                print("Log server is already running")
                return True
            else:
                print("Previous log server process has ended")
                self._log_server_process = None

        try:
            # Get the path to error_transfer.py
            current_dir = pathlib.Path(pathlib.Path(__file__).resolve()).parent
            error_transfer_path = current_dir / "error_transfer.py"

            if not pathlib.Path(error_transfer_path).exists():
                print(
                    f"Error: Could not find error_transfer.py at {error_transfer_path}"
                )
                return False

            print(f"🚀 Starting log server subprocess: {error_transfer_path}")

            # Start the subprocess - choose method based on settings
            log_display_mode = settings.LOG_DISPLAY_MODE

            if log_display_mode == "separate_window":
                # Option 1: Separate console window (recommended)
                if os.name == "nt":  # Windows
                    self._log_server_process = subprocess.Popen(
                        [sys.executable, error_transfer_path],
                        creationflags=subprocess.CREATE_NEW_CONSOLE,
                    )
                else:  # Linux/Mac
                    self._log_server_process = subprocess.Popen(
                        ["gnome-terminal", "--", sys.executable, error_transfer_path]
                    )
            elif log_display_mode == "background":
                # Option 2: Background process (logs not visible)
                self._log_server_process = subprocess.Popen(
                    [sys.executable, error_transfer_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif log_display_mode == "file":
                # Option 3: Log to file
                log_file = (
                    settings.BASE_DIR / "basic_logs" / "error_log.txt"
                )  # Fixed: should be src/basic_logs, not project_root/basic_logs
                print(f"Log file exists: {log_file.exists()}, path: {log_file}")
                with log_file.open("w") as f:
                    self._log_server_process = subprocess.Popen(
                        [sys.executable, error_transfer_path], stdout=f, stderr=f
                    )
                print(f"📝 Log server output will be written to: {log_file}")
            else:
                # Default: Separate window
                if os.name == "nt":  # Windows
                    self._log_server_process = subprocess.Popen(
                        [sys.executable, error_transfer_path],
                        creationflags=subprocess.CREATE_NEW_CONSOLE,
                    )
                else:  # Linux/Mac
                    self._log_server_process = subprocess.Popen(
                        ["gnome-terminal", "--", sys.executable, error_transfer_path]
                    )

            print(f"✅ Log server started with PID: {self._log_server_process.pid}")

            # Give the server a moment to start up
            time.sleep(2)

            # Check if the process is still running
            if self._log_server_process.poll() is None:
                print("✅ Log server is running successfully")
                return True
            else:
                print("❌ Log server failed to start")
                self._log_server_process = None
                return False

        except Exception as e:
            print(f"❌ Failed to start log server: {e}")
            self._log_server_process = None
            return False

    def stop_log_server(self):
        """Stop the log server subprocess with enhanced cleanup"""
        if self._log_server_process is not None:
            try:
                print("🛑 Stopping log server...")

                # Check if process is still alive before terminating
                if self._log_server_process.poll() is None:
                    print(
                        f"Terminating log server process (PID: {self._log_server_process.pid})"
                    )

                    # First try graceful termination
                    self._log_server_process.terminate()

                    # Wait for process to terminate gracefully
                    try:
                        self._log_server_process.wait(timeout=5)  # Increased timeout
                        print("✅ Log server stopped gracefully")
                    except subprocess.TimeoutExpired:
                        print(
                            "⚠️ Log server didn't stop gracefully, forcing termination..."
                        )
                        self._log_server_process.kill()
                        try:
                            self._log_server_process.wait(
                                timeout=3
                            )  # Increased timeout
                            print("✅ Log server forcefully terminated")
                        except subprocess.TimeoutExpired:
                            print("❌ Could not terminate log server process")
                            # Try to clean up any remaining processes
                            try:
                                import psutil

                                parent = psutil.Process(self._log_server_process.pid)
                                for child in parent.children(recursive=True):
                                    child.kill()
                                parent.kill()
                                print("✅ Forcefully killed process tree")
                            except ImportError:
                                print("⚠️ psutil not available for process tree cleanup")
                            except Exception as cleanup_error:
                                print(
                                    f"⚠️ Error during process tree cleanup: {cleanup_error}"
                                )
                else:
                    print("✅ Log server process already terminated")

            except Exception as e:
                print(f"❌ Error stopping log server: {e}")
            finally:
                self._log_server_process = None

                # Also clean up any stale lock files
                try:
                    lock_file = (
                        pathlib.Path(__file__).parent / ".." / ".." / "basic_logs" / "server.lock"
                    )
                    if lock_file.exists():
                        lock_file.unlink()
                        print("🧹 Cleaned up server lock file")
                except Exception as lock_cleanup_error:
                    print(f"⚠️ Error cleaning up lock file: {lock_cleanup_error}")

    def is_log_server_running(self):
        """Check if the log server subprocess is running"""
        if self._log_server_process is None:
            return False
        return self._log_server_process.poll() is None

    def get_socket_connection(self):
        """Get or create the socket connection with adaptive timeout and health checking"""
        if self._cleanup_in_progress:  # Prevent new connections during cleanup
            return None

        # === STEP 1: HEALTH CHECK EXISTING CONNECTION ===
        if self._socket_con is not None:
            if (
                hasattr(self._socket_con, "_is_connected")
                and self._socket_con._is_connected()
            ):
                return self._socket_con
            else:
                print("🔄 Detected dead connection, clearing for reconnection...")
                try:
                    if hasattr(self._socket_con, "client_socket"):
                        self._socket_con.client_socket.close()
                except Exception as e:
                    print(f"❌ Error closing dead socket: {e}")
                self._socket_con = None

        if self._socket_con is None:
            try:
                if not getattr(settings, "ENABLE_SOCKET_LOGGING", False):
                    print("Socket system_logging is disabled in settings")
                    return None

                # First, try to connect to existing server
                socket_req = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                socket_req.settimeout(0.5)
                try:
                    socket_req.connect((settings.SOCKET_HOST, settings.SOCKET_PORT))
                    self._socket_con = SocketCon(socket_req)
                    print("✅ Connected to existing log server")
                    settings.socket_con = self._socket_con  # expose raw connection
                    return self._socket_con
                except (ConnectionRefusedError, socket.timeout):
                    print("📡 No log server found, starting new one...")
                    socket_req.close()
                    if self.start_log_server():
                        time.sleep(1)
                        socket_req = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        socket_req.settimeout(2)
                        socket_req.connect((settings.SOCKET_HOST, settings.SOCKET_PORT))
                        self._socket_con = SocketCon(socket_req)
                        settings.socket_con = self._socket_con
                        print("✅ Connected to newly started log server")
                        return self._socket_con
                    else:
                        print("❌ Failed to start log server")
                        return None
            except Exception as e:
                print(f"❌ Error establishing socket connection: {e}")
                self._socket_con = None
        return self._socket_con

    def send_error(self, message: str):
        """LEGACY: Send error (now bridged to structured protocol)."""
        socket_con = self.get_socket_connection()
        sender = self._build_debug_sender() if socket_con else None
        if sender:
            try:
                # Heuristic parsing for legacy level prefix like [ERROR]
                level = LogLevel.INFO
                heading = "LEGACY • MESSAGE"
                body = message.strip()
                if body.startswith("[") and "]" in body.split("\n", 1)[0]:
                    prefix = body[1 : body.find("]")].upper()
                    body_no_prefix = body[body.find("]") + 1 :].strip()
                    heading = f"LEGACY • {prefix}"
                    body = body_no_prefix or body
                    level_map = {
                        "DEBUG": LogLevel.DEBUG
                        if hasattr(LogLevel, "DEBUG")
                        else LogLevel.INFO,
                        "INFO": LogLevel.INFO,
                        "WARNING": LogLevel.WARNING,
                        "WARN": LogLevel.WARNING,
                        "ERROR": LogLevel.ERROR,
                        "CRITICAL": LogLevel.CRITICAL,
                    }
                    level = level_map.get(prefix, LogLevel.INFO)
                sender.send_debug_message(
                    heading=heading,
                    body=body,
                    level=level,
                    metadata={"origin": "legacy_send_error"},
                )
            except Exception as e:
                print(f"Failed structured send, falling back. Error: {e}")
                if socket_con and hasattr(socket_con, "send_error"):
                    try:
                        socket_con.send_error(message + "\n")
                    except Exception as inner:
                        print(f"Legacy fallback failed: {inner}\nOriginal: {message}")
        else:
            print(f"Socket not available - {message}")

    def is_connected(self):
        """Check if socket connection is active"""
        if self._socket_con and hasattr(self._socket_con, "_is_connected"):
            return self._socket_con._is_connected()
        return False

    def close_connection(self):
        """Close the socket connection and optionally stop the log server"""
        if self._socket_con and hasattr(self._socket_con, "client_socket"):
            try:
                self._socket_con.client_socket.close()
                print("Socket connection closed")
            except Exception as e:
                print(f"Error closing socket: {e}")
        self._socket_con = None
        if self.is_log_server_running():
            print("🔄 Stopping log server subprocess...")
            self.stop_log_server()

    @classmethod
    def cleanup(cls):
        """Simple cleanup - just kill the subprocess"""
        print("🧹 Cleaning up SocketManager...")
        if hasattr(cls, "instance") and cls.instance is not None:
            cls.instance._cleanup_in_progress = True
            instance = cls.instance
            if instance._socket_con:
                try:
                    if hasattr(instance._socket_con, "client_socket"):
                        instance._socket_con.client_socket.close()
                        print("🔌 Socket closed")
                except Exception:
                    pass
                instance._socket_con = None
            if instance._log_server_process is not None:
                try:
                    print("🛑 Killing log server subprocess...")
                    instance._log_server_process.kill()
                    print("✅ Log server killed")
                except Exception as e:
                    print(e)
                finally:
                    instance._log_server_process = None
        print("✅ SocketManager cleanup completed")


# --- Safe Socket Wrapper (merged & enhanced) ---
class SafeSocketWrapper:
    """Safe wrapper for socket connections that prevents NoneType errors and bridges legacy calls."""

    def __init__(self, manager: SocketManager):
        self._manager = manager

    def send_error(self, message: str):  # Legacy external API
        return self._manager.send_error(message)

    def _is_connected(self):
        return self._manager.is_connected()

    # Structured helpers for external callers wanting protocol level access
    def send_debug(self, heading: str, body: str, level: str = "INFO", metadata=None):
        sender = self._manager._build_debug_sender()
        try:
            sender.send_debug_message(heading, body, level, metadata or {})
            return True
        except Exception as e:
            print(f"[SAFE_SOCKET_FALLBACK] {heading}: {body} ({e})")
            return False


# Global instances
socket_manager = SocketManager()
safe_socket = SafeSocketWrapper(socket_manager)

# Ensure settings.socket_con always has something usable for legacy code
try:
    if not hasattr(settings, "socket_con") or settings.socket_con is None:
        settings.socket_con = (
            safe_socket  # Provide wrapper that emulates expected interface
        )
except Exception:
    pass
