from __future__ import annotations
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Callable

# 🔧 Structured diagnostics
try:
    from src.ui.diagnostics.debug_helpers import debug_error, debug_info
    from src.ui.diagnostics.rich_traceback_manager import RichTracebackManager
except ImportError:  # Fallback minimal stubs if diagnostics not yet loaded

    def debug_error(heading: str, body: str, metadata=None):
        print(f"[ERROR] {heading}: {body} | {metadata}")

    def debug_info(heading: str, body: str, metadata=None):
        print(f"[INFO] {heading}: {body} | {metadata}")

    class RichTracebackManager:  # type: ignore
        @staticmethod
        def handle_exception(e, context: str = "", extra_context=None):
            import traceback

            print(f"[TRACEBACK] {context}: {e}\n{traceback.format_exc()}")


class EventListener:
    """A simple event listener system to handle different types of events."""

    class EventType(Enum):
        """Enum for different event types."""

        VARIABLE_CHANGED = "variable_changed"
        ERROR_OCCURRED = "error_occurred"  # Placeholder for future implementation

    @dataclass
    class EventData:
        """
        🎯 ULTIMATE SIMPLIFICATION

        Minimal event data container with flexible metadata.
        """

        event_type: "EventListener.EventType"
        source_class: type
        timestamp: float = None
        meta_data: Dict[str, Any] = None

        def __post_init__(self):
            if self.timestamp is None:
                import time

                self.timestamp = time.time()
            if self.meta_data is None:
                self.meta_data = {}
            if not isinstance(self.event_type, EventListener.EventType):
                raise ValueError(
                    "event_type must be an instance of EventListener.EventType"
                )

    class EventManager:
        """Manages event listeners and dispatches events with structured diagnostics."""

        _instance = None
        _lock = threading.Lock()

        def __new__(cls):
            if cls._instance is None:
                cls._instance = super(EventListener.EventManager, cls).__new__(cls)
                cls._instance.listeners = {}
            return cls._instance

        def __init__(self):
            if not hasattr(self, "initialized"):
                self.initialized = True
                self.listeners: Dict[EventListener.EventType, List[Callable]] = {}
                # Store priority per (event_type, listener) for granularity
                self.listener_priority: Dict[tuple, int] = {}
                self.listener_filter: Dict[Callable, Callable] = {}

        def register_listener(
            self,
            event_type: "EventListener.EventType",
            listener: Callable[[EventListener.EventData],...],
            priority: int = 0,
            filter_func: Callable = None,
        ) -> None:
            """
            Register a listener callback for a specific event type.

            Validation added: listener MUST be callable (prevents '__name__' errors on str / bad inputs).
            """
            with self._lock:
                if not callable(listener):
                    raise TypeError(
                        f"Listener for {event_type} must be callable, got {type(listener).__name__}: {listener!r}"
                    )

                if event_type not in self.listeners:
                    self.listeners[event_type] = []

                self.listeners[event_type].append(listener)
                self.listener_priority[(event_type, listener)] = priority
                if filter_func:
                    self.listener_filter[listener] = filter_func

                # Sort listeners per event by individual priority (higher first)
                self.listeners[event_type].sort(
                    key=lambda l: self.listener_priority.get((event_type, l), 0),
                    reverse=True,
                )
                debug_info(
                    heading="EVENT_LISTENER • REGISTERED",
                    body=f"Listener registered for {event_type.name}",
                    metadata={
                        "listener": getattr(listener, "__name__", repr(listener)),
                        "priority": priority,
                    },
                )

        def unregister_listener(
            self, event_type: "EventListener.EventType", listener: Callable
        ) -> None:
            """Unregister a listener for a given event type."""
            with self._lock:
                if (
                    event_type in self.listeners
                    and listener in self.listeners[event_type]
                ):
                    self.listeners[event_type].remove(listener)
                    self.listener_priority.pop((event_type, listener), None)
                    self.listener_filter.pop(listener, None)
                    debug_info(
                        heading="EVENT_LISTENER • UNREGISTERED",
                        body=f"Listener removed for {event_type.name}",
                        metadata={
                            "listener": getattr(listener, "__name__", repr(listener))
                        },
                    )

        def emit_event(self, event_data: "EventListener.EventData") -> None:
            """
            Emit an event synchronously to all registered listeners.

            Errors are NO LONGER suppressed: they are logged and re-raised after structured reporting.
            """
            with self._lock:
                listeners = list(self.listeners.get(event_data.event_type, []))

            for listener in listeners:
                # Apply filter before invocation
                filter_func = self.listener_filter.get(listener)
                try:
                    if filter_func and not filter_func(event_data):
                        continue
                except Exception as filter_err:
                    listener_name = getattr(listener, "__name__", repr(listener))
                    RichTracebackManager.handle_exception(
                        filter_err,
                        context="EventListener Filter Evaluation",
                        extra_context={
                            "listener": listener_name,
                            "event_type": event_data.event_type.name,
                            "meta_keys": list(event_data.meta_data.keys())
                            if event_data.meta_data
                            else [],
                        },
                    )
                    debug_error(
                        heading="EVENT_LISTENER • FILTER_ERROR",
                        body=f"Filter failed for listener {listener_name}",
                        metadata={"error": str(filter_err)},
                    )
                    # Continue to next listener; filter failure shouldn't kill dispatch
                    continue

                # Invoke listener
                try:
                    listener(event_data)
                except Exception as e:
                    listener_name = getattr(listener, "__name__", repr(listener))
                    # Full traceback to diagnostics
                    RichTracebackManager.handle_exception(
                        e,
                        context="EventListener Callback Execution",
                        extra_context={
                            "listener": listener_name,
                            "event_type": event_data.event_type.name,
                            "meta_data": event_data.meta_data,
                            "source_class": getattr(
                                event_data.source_class,
                                "__name__",
                                repr(event_data.source_class),
                            ),
                        },
                    )
                    debug_error(
                        heading="EVENT_LISTENER • CALLBACK_ERROR",
                        body=f"Unhandled exception in listener {listener_name}",
                        metadata={
                            "event_type": event_data.event_type.name,
                            "error_type": type(e).__name__,
                            "error": str(e),
                        },
                    )
                    # Re-raise so errors are NOT silently suppressed
                    raise

        def emit_async(self, event_data: "EventListener.EventData") -> None:
            """
            Emit an event asynchronously in a daemon thread.

            Exceptions inside listeners will still propagate after being logged, terminating that thread.
            """

            def _runner():
                try:
                    self.emit_event(event_data)
                except Exception:
                    # Already logged in emit_event; nothing extra here
                    pass

            thread = threading.Thread(target=_runner, daemon=True)
            thread.start()


# Global event manager instance
event_manager = EventListener.EventManager()
