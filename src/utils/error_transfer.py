import atexit
import os
import signal
import socket
import sys
import threading
from pathlib import Path

from anyio import sleep

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import settings
from src.utils.sound import beep
from src.ui.rich_error_print import RichErrorPrint
from rich.console import Console


class SocketCon:
    got_killed: bool = None  # Flag to indicate if the server was killed
    _lock = threading.Lock()

    def __init__(self, _client_socket: socket.socket):
        with self._lock:
            self.client_socket = _client_socket

    def send_error(self, error_message: str, close_socket: bool = False):
        if "\n" not in  error_message:
            error_message += "\n" # Ensure message ends with newline easy to parse in the receiver
        with self._lock:
            try:
                #     check whether the socket is connected
                if not self._is_connected():
                    print(error_message, flush=True, file=sys.stderr)
                    raise socket.error("Socket is not connected.")
                # Send the error message
                else:
                    # print("Sending error message: ", error_message, flush=True, file=sys.stderr)
                    # beep(7933, 500)  # Beep sound for error notification
                    self.client_socket.sendall(error_message.encode("utf-8"))
                # self.client_socket.sendall(error_message.encode('utf-8'))
            except socket.error as e:
                if str(e) == "Socket is not connected.":
                    pass
                else:
                    print(f"Error sending message: {e}")
            finally:
                if close_socket:
                    self.client_socket.close()

    def receive_error(self) -> str:
        try:
            data = self.client_socket.recv(1024 * 1024)  # Receive up to 1 MB of data
            return data.decode("utf-8")
        except socket.error as e:
            print(f"Error receiving message: {e}")
            return ""

    def _is_connected(self):
        try:
            # Use getsockopt to check socket state without sending data
            # This works for both unidirectional and bidirectional connections
            error = self.client_socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            if error:
                return False

            # Additional check: see if socket is still connected
            # This uses a more reliable method that doesn't send data
            try:
                # Check if socket is readable (has data or is closed)
                import select

                ready, _, _ = select.select([self.client_socket], [], [], 0)
                if ready:
                    # Socket is readable - peek at data without consuming it
                    data = self.client_socket.recv(1, socket.MSG_PEEK)
                    return len(data) > 0  # If no data, connection is closed
                return True  # Socket exists and no error
            except socket.error:
                return False
        except socket.error:
            return False
        except Exception as e:
            print(f"Unexpected error in connection check: {e}")
            return False


def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    print(f"Received signal {signum}, shutting down server...")
    SocketCon.got_killed = True


def cleanup_lock_file():
    """Remove lock file on exit"""
    lock_file = settings.BASE_DIR / "basic_logs" / "server.lock"
    try:
        if Path(lock_file).exists():
            Path(lock_file).unlink()
            print("Lock file removed")
    except Exception as e:
        print(f"Error removing lock file: {e}")


def create_lock_file():
    """Create lock file to prevent multiple instances"""
    lock_file = settings.BASE_DIR / "basic_logs" / "server.lock"
    # Check if another instance is already running
    if Path(lock_file).exists():
        try:
            with lock_file.open("r") as f:
                pid = int(f.read().strip())

            # Check if the process is still running
            try:
                os.kill(pid, 0)  # This doesn't kill, just checks if process exists
                print(f"Another server instance is already running (PID: {pid})")
                return False
            except OSError:
                # Process doesn't exist, remove stale lock file
                Path(lock_file).unlink()
                print("Removed stale lock file")
        except (ValueError, FileNotFoundError):
            # Invalid or missing lock file, remove it
            try:
                Path(lock_file).unlink()
            except Exception as e:
                print(f"Error removing stale lock file: {e}")
                pass

    # Create new lock file
    try:
        Path(Path(lock_file).parent).mkdir(exist_ok=True, parents=True)
        with lock_file.open("w") as f:
            f.write(str(os.getpid()))
        print(f"Created lock file with PID: {os.getpid()}")
        return True
    except Exception as e:
        print(f"Error creating lock file: {e}")
        return False


def write_to_file(text: str, mode="a"):
    """Write text to a file in the basic_logs directory"""
    file_path = settings.BASE_DIR / "basic_logs" / "error_log.txt"
    w_lock = threading.Lock()  # Use a lock to prevent concurrent writes
    with w_lock:
        try:
            with file_path.open(mode, encoding="utf-8") as f:
                f.write("\n" + text + "\n")
        except Exception as we:
            print_error.print_rich(f"[Error] Writing to file failed: {we}")
    pass


def new_logger_write(text: str):
    """
    Process incoming debug messages and dispatch to logging system.
    Converts DebugMessage protocol to LogEntry protocol before dispatching.
    """
    try:
        # Use absolute imports to work when run as __main__
        from src.system_logging.dispatcher import Dispatcher
        from src.system_logging.adapter import ProtocolAdapter

        # Convert DebugMessage JSON to LogEntry JSON
        # parse multiple messages if present
        messages = text.strip().split("\n")
        for message in messages:
            converted_json = ProtocolAdapter.convert_to_log_entry_json(message)

            # Dispatch to logging system
            disp = Dispatcher()
            disp.dispatch(converted_json)

    except ImportError as e:
        # If system_logging not available, fall back to file write
        print(f"[IMPORT_ERROR] Logging system not available: {e}", file=sys.stderr)
        write_to_file(text)
    except Exception as e:
        # Catch-all for unexpected errors
        print(f"[LOGGER_ERROR] {e}", file=sys.stderr)
        write_to_file(text)


if __name__ == "__main__":
    # Check for existing instance and create lock file
    if not create_lock_file():
        print("Exiting: Another server instance is already running")
        sys.exit(1)

    # Register logging handlers for this subprocess
    try:
        from src.system_logging.on_time_registry import OnTimeRegistry
        from src.system_logging.handlers.handler_base import TextHandler

        registry = OnTimeRegistry()
        registry.register(TextHandler())
        print("✅ Logging handlers registered in error_transfer subprocess")
    except Exception as e:
        print(f"⚠️  Could not register logging handlers: {e}")
        # Continue anyway - will fall back to write_to_file

    # Register cleanup function
    atexit.register(cleanup_lock_file)
    try:
        console = Console(
            force_terminal=True,
            color_system="windows",  # Better Windows compatibility
            width=120,  # Default width if not specified
            legacy_windows=False,  # Use modern Windows console features
            safe_box=True,  # Safe box drawing for Windows
            highlight=True,  # Enable syntax highlighting
            emoji=True,  # Enable emoji support
            markup=True,  # Enable Rich markup
            log_time=True,  # Add timestamps to logs
            log_path=False,
        )  # Don't show file paths in logs  # Initialize rich console for system_logging
        settings.debug_console = console  # Set debug console for the application
        print_error = RichErrorPrint(console)  # Initialize rich error printing
    except Exception as e:
        print(f"Error initializing console: {e}", flush=True, file=sys.stderr)
        sleep(10)

    # Set up signal handlers for graceful shutdown
    try:
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        # On Windows, also handle SIGBREAK
        if hasattr(signal, "SIGBREAK"):
            signal.signal(signal.SIGBREAK, signal_handler)
    except Exception as e:
        print(f"Warning: Could not set up signal handlers: {e}")

    # Initialize server
    server_socket = None
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
        )  # Allow socket reuse
        server_socket.bind(("localhost", 5390))
        server_socket.listen(1)
        server_socket.settimeout(
            1
        )  # Shorter timeout to check got_killed flag more frequently
        listening = True
        SocketCon.got_killed = False  # Flag to indicate if the server was killed

        # write_to_file("", mode="w")  # Clear the log file on startup (now removed and replaced by new logging system)
        print_error.print_rich("Server is listening...")

        while listening and not SocketCon.got_killed:
            try:
                client_socket, addr = server_socket.accept()
                print_error.print_rich(f"Connection from {addr}")
                try:
                    socket_con = SocketCon(client_socket)
                    while not SocketCon.got_killed and client_socket:
                        received_error = socket_con.receive_error()
                        if not received_error:
                            print_error.print_rich(
                                "No data received, closing connection."
                            )
                            break  # Client disconnected or error occurred
                        if isinstance(received_error, str):
                            # Split by newline to handle multiple messages sent together
                            # TCP may concatenate multiple sends into one recv()
                            messages = received_error.split('\n')

                            for single_message in messages:
                                single_message = single_message.strip()
                                if not single_message:  # Skip empty lines
                                    continue

                                # Display each message separately in Rich console
                                print_error.print_rich(f"{single_message}")

                                # Legacy logging (write to error_log.txt)
                                # write_to_file(single_message) # now get removed and successfully replaced by new logging system

                                # New categorized logging system
                                new_logger_write(single_message)
                        else:
                            print_error.print_rich(received_error)
                        if settings.ENABLE_SOUND_NOTIFICATIONS:
                            beep(7933, 500)  # Beep sound for error notification
                    # Don't exit the loop - continue listening for new connections
                    print_error.print_rich(
                        "Client disconnected, waiting for new connections..."
                    )
                finally:
                    client_socket.close()
                    write_to_file("Connection closed with client.")
            except socket.timeout:
                # Check got_killed flag on timeout and continue if not killed
                if SocketCon.got_killed:
                    print_error.print_rich("Server shutdown requested, exiting...")
                    break
                continue  # Continue listening if not killed
            except Exception as e:
                if not SocketCon.got_killed:
                    print_error.print_rich(f"accepting connection: {e}")
                break

    except Exception as e:
        print_error.print_rich(f"Server encountered an error: {e}")
        sleep(2)  # Wait before exiting to allow error message to be seen
    finally:
        if server_socket:
            print("Closing server socket...")
            server_socket.close()
        cleanup_lock_file()
        print("Server shutdown complete.")