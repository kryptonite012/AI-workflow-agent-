# 🎨 Rich Traceback Manager - Comprehensive Error Handling System
"""
Rich Traceback Manager for AI-Agent-Workflow Project

This module provides centralized rich traceback functionality across the entire application.
It enhances error handling with beautiful, informative tracebacks that show:
- Exact line numbers and file locations
- Variable values at the time of error
- Call stack with context
- Syntax highlighting for better readability
- Integration with socket system_logging system

Usage:
    from src.ui.diagnostics.rich_traceback_manager import RichTracebackManager

    # Initialize at application start
    RichTracebackManager.initialize()

    # Use in try-catch blocks
    try:
        risky_operation()
    except Exception as e:
        RichTracebackManager.handle_exception(e, context="Operation description")
"""

import inspect
import pathlib
import sys
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, Callable

from rich.console import Console
from rich.traceback import install, Traceback


# Import settings for socket integration


class RichTracebackManager:
    """
    Centralized Rich Traceback Manager for enhanced error handling across the application.

    Features:
    - Beautiful, informative tracebacks with syntax highlighting
    - Integration with socket system_logging system
    - Context-aware error reporting
    - Variable inspection at error points
    - Automatic error categorization
    - Performance impact tracking
    """

    _initialized = False
    _console: Optional[Console] = None
    _error_count = 0
    _error_categories: Dict[str, int] = {}
    _handling_exception: bool = False  # re-entrancy guard

    @classmethod
    def initialize(
        cls,
        show_locals: bool = False,  # Disabled by default for cleaner main process
        max_frames: int = 10,
        suppress_modules: Optional[list] = None,
    ) -> None:
        """
        Initialize Rich Traceback system for MAIN PROCESS ONLY.
        This only sets up basic error tracking - actual display happens in debug process.

        Args:
            show_locals: Show local variables in traceback (disabled for main process)
            max_frames: Maximum number of frames to show
            suppress_modules: List of modules to suppress in traceback
        """
        # Set up default suppressed modules
        if suppress_modules is None:
            suppress_modules = [
                "click",
                "rich",
                "__main__",
                "runpy",
                "threading",
                "concurrent.futures",
                "asyncio",
                "socket",
                "pickle",
            ]

        # NO CONSOLE INITIALIZATION - we only handle error tracking in main process
        # Visual display happens in separate debug process
        cls._console = None  # Explicitly set to None

        # Set up exception hook for uncaught exceptions
        sys.excepthook = cls._global_exception_handler

        cls._initialized = True

        # Route initialization log to debug console
        try:
            from src.ui.diagnostics.debug_helpers import debug_info

            debug_info(
                heading="SYSTEM • RICH_TRACEBACK",
                body="Rich Traceback Manager initialized for main process (display via debug console)",
                metadata={
                    "process_type": "main",
                    "show_locals": show_locals,
                    "max_frames": max_frames,
                },
            )
        except Exception:
            # Fallback only if debug_helpers not available during early initialization
            pass

    @classmethod
    def initialize_debug_process(
        cls,
        debug_console: Console,
        show_locals: bool = False,
        max_frames: int = 10,
        theme: str = "monokai",
        extra_lines: int = 1,
        suppress_modules: Optional[list] = None,
    ) -> None:
        """
        Initialize Rich Traceback system for DEBUG PROCESS ONLY.
        This sets up the actual Rich console for beautiful traceback display.

        Args:
            debug_console: Console instance for debug process
            show_locals: Show local variables in traceback
            max_frames: Maximum number of frames to show
            theme: Syntax highlighting theme
            extra_lines: Extra lines of context around error
            suppress_modules: List of modules to suppress in traceback
        """
        # Set up default suppressed modules
        if suppress_modules is None:
            suppress_modules = [
                "click",
                "rich",
                "__main__",
                "runpy",
                "threading",
                "concurrent.futures",
                "asyncio",
                "socket",
                "pickle",
            ]

        # Set console for debug process
        cls._console = debug_console

        # Install rich traceback globally for debug process
        install(
            console=debug_console,
            show_locals=show_locals,
            max_frames=max_frames,
            extra_lines=extra_lines,
            word_wrap=False,  # Disabled for cleaner display
            indent_guides=True,
            suppress=suppress_modules,
        )

        cls._initialized = True

        # Route debug process initialization log to debug console
        try:
            from src.ui.diagnostics.debug_helpers import debug_info

            debug_info(
                heading="SYSTEM • RICH_TRACEBACK",
                body="Rich Traceback Manager initialized for debug process with visual display",
                metadata={
                    "process_type": "debug",
                    "show_locals": show_locals,
                    "max_frames": max_frames,
                    "theme": theme,
                },
            )
        except Exception:
            # Fallback only if debug_helpers not available during early initialization
            pass

    @classmethod
    def _global_exception_handler(cls, exc_type, exc_value, exc_traceback):
        """
        Global exception handler for uncaught exceptions.
        """
        if issubclass(exc_type, KeyboardInterrupt):
            # Handle Ctrl+C gracefully
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # ✅ Handle encoding errors from Sentry/subprocess threads
        if issubclass(exc_type, UnicodeDecodeError):
            # These are usually from Sentry SDK subprocess monitoring
            # Log to debug console but don't crash the application
            from src.ui.diagnostics.debug_helpers import debug_warning

            debug_warning(
                heading="SYSTEM • UNICODE_ERROR",
                body=f"Unicode Encoding Error in subprocess: {str(exc_value)[:100]}...",
                metadata={"error_type": "UnicodeEncodeError", "context": "subprocess"},
            )
            return  # Don't crash the app for encoding issues

        # ✅ Handle thread exceptions gracefully
        if "Thread-" in str(exc_traceback) or "_readerthread" in str(exc_traceback):
            # These are background thread errors, usually from Sentry monitoring
            from src.ui.diagnostics.debug_helpers import debug_warning

            debug_warning(
                heading="SYSTEM • THREAD_ERROR",
                body=f"Background Thread Error: {exc_type.__name__}: {str(exc_value)[:100]}...",
                metadata={
                    "error_type": exc_type.__name__,
                    "context": "background_thread",
                },
            )
            return  # Don't crash the app for background thread issues

        cls.handle_exception(
            exc_value,
            context="Uncaught Exception",
            exc_type=exc_type,
            exc_traceback=exc_traceback,
        )

    @classmethod
    def handle_exception(
        cls,
        exception: Exception,
        context: str = "Unknown Context",
        exc_type: Optional[type] = None,
        exc_traceback: Optional[Any] = None,
        show_locals: bool = True,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Handle and display exception with rich formatting.

        Args:
            exception: The exception that occurred
            context: Description of what was happening when error occurred
            exc_type: Exception type (auto-detected if None)
            exc_traceback: Exception traceback (auto-detected if None)
            show_locals: Whether to show local variables
            extra_context: Additional context information to display
        """
        # Re-entrancy guard to prevent infinite recursion
        if getattr(cls, "_handling_exception", False):
            try:
                # Route recursion fallback to debug console
                from src.ui.diagnostics.debug_helpers import debug_warning

                debug_warning(
                    heading="SYSTEM • RECURSION_GUARD",
                    body=f"Rich Traceback recursion prevented: {type(exception).__name__}: {str(exception)[:120]}",
                    metadata={"context": context, "recursion_guard": True},
                )
            except Exception:
                # Ultimate fallback - but this should rarely happen
                pass
            return
        cls._handling_exception = True
        try:
            if not cls._initialized:
                raise RuntimeError(
                    "RichTracebackManager not initialized. Call initialize() first."
                )

            # Auto-detect exception info if not provided
            if exc_type is None or exc_traceback is None:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                if exc_value is None:
                    exc_value = exception

            # Increment error tracking
            cls._error_count += 1
            error_category = exc_type.__name__ if exc_type else type(exception).__name__
            cls._error_categories[error_category] = (
                cls._error_categories.get(error_category, 0) + 1
            )

            # Create rich traceback with cleaner formatting
            if exc_traceback:
                rich_traceback = Traceback.from_exception(
                    exc_type,
                    exception,
                    exc_traceback,
                    show_locals=False,  # Always disabled for cleaner display
                    max_frames=8,  # Limit frames for readability
                    width=130,  # Wider for better display
                )
            else:
                # Fallback for cases where traceback is not available
                rich_traceback = Traceback(
                    trace=traceback.extract_tb(sys.exc_info()[2])
                    if sys.exc_info()[2]
                    else [],
                    exc_type=exc_type.__name__
                    if exc_type
                    else type(exception).__name__,
                    exc_value=str(exception),
                    show_locals=False,  # Always disabled for cleaner display
                    max_frames=8,  # Limit frames for readability
                    width=130,  # Wider for better display
                )

            # Create error panel with context
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Build context information
            context_info = [
                f"🕒 Time: {timestamp}",
                f"📍 Context: {context}",
                f"🔢 Error #{cls._error_count}",
                f"📊 Category: {error_category}",
            ]

            # Add extra context if provided
            if extra_context:
                context_info.append("📋 Additional Context:")
                for key, value in extra_context.items():
                    context_info.append(f"   • {key}: {value}")

            # Add caller information
            caller_info = cls._get_caller_info()
            if caller_info:
                context_info.extend(
                    [
                        "📞 Called from:",
                        f"   • File: {caller_info['file']}",
                        f"   • Function: {caller_info['function']}",
                        f"   • Line: {caller_info['line']}",
                    ]
                )

            context_text = "\n".join(context_info)

            # Display the error - ONLY to debug console, never to user window
            # TODO currently we are not sending the panel to the debug window instead we are printing the error (this could be changed later)
            # Use simple print instead of panel sending
            try:
                from src.ui.diagnostics.debug_helpers import debug_error

                # Print error content directly instead of sending panel
                error_content = f"🚨 {error_category}: {str(exception)}\n\nContext: {context_text}\n\nTraceback:\n{traceback.format_exc()}"
                print(f"[RICH_TRACEBACK_ERROR] {error_content}")
                # now send the error to the debug console
                debug_error(
                    heading=error_category,
                    body=f"{str(exception)}\n\n{rich_traceback}",
                    metadata={
                        "context": context,
                        "error_category": error_category,
                        "error_count": cls._error_count,
                        "caller_info": caller_info if caller_info else None,
                    },
                )

            except Exception as debug_error_exception:
                # Fallback to structured debug message if rich panel fails
                try:
                    from src.ui.diagnostics.debug_helpers import debug_error

                    debug_error(
                        heading="RICH_TRACEBACK • ERROR",
                        body=f"{error_category}: {str(exception)}",
                        metadata={
                            "context": context,
                            "error_category": error_category,
                            "error_count": cls._error_count,
                            "panel_error": str(debug_error_exception),
                        },
                    )
                except Exception:
                    # Ultimate fallback - route to debug console via socket if available
                    try:
                        from src.config import settings

                        if hasattr(settings, "socket_con") and settings.socket_con:
                            fallback_msg = f"🚨 ERROR #{cls._error_count}: {error_category} in {context} - {str(exception)}"
                            settings.socket_con.send_error(fallback_msg)
                        else:
                            # Only print to console if absolutely no other option
                            pass  # Suppress console output to prevent user window spam
                    except Exception:
                        # Suppress all output to prevent user window spam
                        pass
        finally:
            cls._handling_exception = False

    @classmethod
    def _get_caller_info(cls) -> Optional[Dict[str, str]]:
        """
        Get information about the caller that triggered the exception.
        """
        try:
            # Get the current frame
            frame = inspect.currentframe()
            if frame is None:
                return None

            # Go up the call stack to find the actual caller
            # Skip our own frames and rich/traceback frames
            while frame:
                frame = frame.f_back
                if frame is None:
                    break

                filename = frame.f_code.co_filename
                function_name = frame.f_code.co_name
                line_number = frame.f_lineno

                # Skip internal frames
                if any(skip in filename for skip in ["rich", "traceback", __file__]):
                    continue

                # Skip if it's in site-packages (external libraries)
                if "site-packages" in filename:
                    continue

                return {
                    "file": pathlib.Path(filename).name,
                    "function": function_name,
                    "line": str(line_number),
                    "full_path": filename,
                }

            return None
        except Exception:
            return None

    @classmethod
    def create_context_decorator(cls, context_name: str):
        """
        Create a decorator that automatically adds context to exceptions.

        Args:
            context_name: Name of the context for error reporting

        Returns:
            Decorator function
        """

        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Get function signature for additional context
                    sig = inspect.signature(func)
                    bound_args = sig.bind(*args, **kwargs)
                    bound_args.apply_defaults()

                    extra_context = {
                        "function": func.__name__,
                        "module": func.__module__,
                        "arguments": {
                            k: str(v)[:100] for k, v in bound_args.arguments.items()
                        },
                    }

                    cls.handle_exception(
                        e,
                        context=f"{context_name} -> {func.__name__}",
                        extra_context=extra_context,
                    )
                    raise  # Re-raise the exception

            return wrapper

        return decorator

    @classmethod
    def log_performance_warning(
        cls, operation: str, duration: float, threshold: float = 1.0
    ):
        """
        Log performance warnings - sent to debug console only.

        Args:
            operation: Description of the operation
            duration: Time taken in seconds
            threshold: Warning threshold in seconds
        """
        if duration > threshold:
            # Send performance warning to debug console via socket
            warning_message = (
                f"[warning]⚠️ Performance Warning: {operation} took {duration:.2f}s "
                f"(threshold: {threshold:.2f}s, exceeded by: {duration - threshold:.2f}s)"
            )

            from src.ui.diagnostics.debug_helpers import debug_performance_warning

            debug_performance_warning(
                operation="error_handling",
                duration=duration,
                threshold=threshold,
                context="rich_traceback_manager",
                metadata={"warning_type": "performance_threshold_exceeded"},
            )
            # No fallback to prevent user window spam

    @classmethod
    def get_error_statistics(cls) -> Dict[str, Any]:
        """
        Get error statistics for debugging and monitoring.

        Returns:
            Dictionary with error statistics
        """
        return {
            "total_errors": cls._error_count,
            "error_categories": cls._error_categories.copy(),
            "most_common_error": max(cls._error_categories.items(), key=lambda x: x[1])[
                0
            ]
            if cls._error_categories
            else None,
            "initialized": cls._initialized,
        }

    @classmethod
    def reset_statistics(cls):
        """
        Reset error statistics (useful for testing or periodic resets).
        """
        cls._error_count = 0
        cls._error_categories.clear()

        from src.ui.diagnostics.debug_helpers import debug_info

        debug_info(
            heading="SYSTEM • STATISTICS",
            body="Error statistics reset",
            metadata={"action": "reset_error_statistics"},
        )

    @classmethod
    def create_safe_wrapper(cls, func: Callable, context: str, default_return=None):
        """
        Create a safe wrapper that catches exceptions and returns a default value.

        Args:
            func: Function to wrap
            context: Context description for error reporting
            default_return: Value to return if exception occurs

        Returns:
            Wrapped function
        """

        def safe_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                cls.handle_exception(e, context=f"Safe Wrapper: {context}")
                return default_return

        return safe_func


# Ensure decorator and helper exist for external imports


def rich_exception_handler(context_name: str):
    """Decorator to wrap functions with RichTracebackManager error handling with added context."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                RichTracebackManager.handle_exception(
                    e,
                    context=context_name,
                    extra_context={
                        "wrapped_function": getattr(func, "__name__", "unknown"),
                        "module": getattr(func, "__module__", "unknown"),
                    },
                )
                raise

        wrapper.__name__ = getattr(func, "__name__", "wrapped")
        return wrapper

    return decorator


def safe_execute(callable_obj, *args, **kwargs):
    """Execute a callable capturing and routing exceptions through RichTracebackManager."""
    try:
        return callable_obj(*args, **kwargs)
    except Exception as e:
        RichTracebackManager.handle_exception(
            e,
            context=f"safe_execute -> {getattr(callable_obj, '__name__', 'callable')}",
            extra_context={"args_len": len(args), "kwargs_keys": list(kwargs.keys())},
        )
        raise
