import atexit
import signal
from typing import Callable, List

# Socket connection now centralized in settings
from src.config import settings


# this is cleanup code for the chat system
class ChatDestructor:
    """
    Handles the cleanup of chat resources, ensuring that all models are stopped and resources are released.
    also clean other resources that might be used during the chat session. like socket connections, files, etc.
    This is typically called when the chat session ends or when the application is exiting.
    """

    is_cleaned_registered = False
    _cleanup_executed = False  # Flag to prevent double cleanup execution
    _all_functions: List[Callable] = []  # Function to be called for cleanup, if any
    _original_sigint_handler = None  # Original SIGINT handler
    _original_sigterm_handler = None  # Original SIGTERM handler

    @classmethod
    def add_destroyer_function(cls, function: Callable):
        """
        Add a cleanup function to be called during the cleanup process.
        :param function: A callable function that performs cleanup.
        """
        if (
            function
            and callable(function)
            and function not in ChatDestructor._all_functions
        ):
            ChatDestructor._all_functions.append(function)
        else:
            raise ValueError("Provided function is not callable")

    @classmethod
    def register_cleanup_handlers(cls):
        """
        Register cleanup handlers for graceful shutdown.
        This ensures models are stopped even during abrupt termination.
        """
        if cls.is_cleaned_registered:
            if settings.socket_con:
                settings.socket_con.send_error(
                    "[LOG]Cleanup handlers already registered."
                )
            return

        # Register atexit handler (called during normal Python exit)
        atexit.register(cls.call_all_cleanup_functions)

        # Register signal handlers for termination signals
        try:
            # Store original handlers before overwriting
            cls._original_sigint_handler = signal.signal(
                signal.SIGINT, cls._signal_handler
            )  # Ctrl+C
            cls._original_sigterm_handler = signal.signal(
                signal.SIGTERM, cls._signal_handler
            )  # Termination signal

            if hasattr(signal, "SIGBREAK"):  # Windows specific
                signal.signal(signal.SIGBREAK, cls._signal_handler)
        except (OSError, ValueError) as e:
            print(f"Could not register signal handler: {e}")

        cls.is_cleaned_registered = True
        if settings.socket_con:
            settings.socket_con.send_error(
                "[LOG]✅ Chat cleanup handlers registered successfully"
            )

    @classmethod
    def _signal_handler(cls, signum, frame):
        """
        Handle termination signals and ensure proper cleanup.
        """
        if settings.socket_con:
            settings.socket_con.send_error(
                f"🛑 Signal {signum} received, cleaning up models..."
            )
        cls.call_all_cleanup_functions()

        # Call original handler if it existed
        if signum == signal.SIGINT and cls._original_sigint_handler:
            cls._original_sigint_handler(signum, frame)
        elif signum == signal.SIGTERM and cls._original_sigterm_handler:
            cls._original_sigterm_handler(signum, frame)
        else:
            # Default termination
            signal.default_int_handler(signum, frame)

    @classmethod
    def call_all_cleanup_functions(cls):
        # Prevent double cleanup execution
        if cls._cleanup_executed:
            if settings.socket_con:
                settings.socket_con.send_error(
                    "[LOG]Cleanup already executed, skipping."
                )
            return

        cls._cleanup_executed = True  # Set flag to prevent re-execution

        if len(cls._all_functions) == 0:
            if settings.socket_con:
                settings.socket_con.send_error("[LOG]No cleanup functions registered.")
            return

        if settings.socket_con:
            settings.socket_con.send_error("[LOG]🧹 Starting cleanup process...")

        terminated_count = 0
        for func in cls._all_functions:
            try:
                if callable(func):
                    if settings.socket_con:
                        settings.socket_con.send_error(
                            f"[LOG]Executing cleanup: {func.__name__}"
                        )
                    func()  # Call the cleanup function
                    terminated_count += 1
                else:
                    print(f"[LOG]Function {func} is not callable, skipping.")
            except Exception as e:
                error_msg = f"[LOG]Error during cleanup function {func.__name__ if hasattr(func, '__name__') else func}: {e}"
                if settings.socket_con:
                    settings.socket_con.send_error(error_msg)
                else:
                    print(error_msg)

        if settings.socket_con:
            settings.socket_con.send_error(
                f"[LOG]✅ Cleanup completed. {terminated_count} functions executed."
            )
        else:
            print(f"[LOG]✅ Cleanup completed. {terminated_count} functions executed.")
