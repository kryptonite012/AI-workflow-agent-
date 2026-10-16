import threading
from dataclasses import dataclass
from enum import Enum
from symtable import Class
from typing import Any, Dict, List, Callable


class EventListener:
    """A simple event listener system to handle different types of events."""

    class EventType(Enum):
        """Enum for different event types."""

        VARIABLE_CHANGED = "variable_changed"
        STATUS_CHANGED = "status_changed"
        ERROR_OCCURRED = "error_occurred"

    @dataclass
    class EventData:
        """Data structure for event data."""

        event_type: "EventListener.EventType"
        source_class: type
        variable_name: str = None
        old_value: Any = None
        new_value: Any = None
        time_stamp: float = None
        meta_data: Dict[str, Any] = None

    class EventManager:
        """Manages event listeners and dispatches events."""

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
                self.listener_priority: Dict[EventListener.EventType, int] = {}
                self.listener_filter: Dict[Callable, Callable] = {}

        def register_listener(
            self,
            event_type: "EventListener.EventType",
            listener: Callable,
            priority: int = 0,
            filter_func: Callable = None,
        ) -> None:
            """
            Registers a listener for a specific event type.

            Args:
                event_type (`EventListener.EventType`): The type of event to listen for.
                listener (Callable): The callback function to invoke when the event occurs.
                priority (int, optional): Determines the order of execution; higher values are called first. Defaults to 0.
                filter_func (Callable, optional): An optional function to filter events before invoking the listener.

            Raises:
                ValueError: If the listener is not callable.

            Returns:
                None
            """
            with self._lock:
                if event_type not in self.listeners:
                    self.listeners[event_type] = []

                self.listeners[event_type].append(listener)
                self.listener_priority[event_type] = priority
                if filter_func:
                    self.listener_filter[listener] = filter_func

                # Sort listeners by priority
                self.listeners[event_type].sort(
                    key=lambda l: self.listener_priority.get(l, 0), reverse=True
                )

        def unregister_listener(
            self, event_type: "EventListener.EventType", listener: Callable
        ) -> None:
            """
            Unregisters a listener for a specific event type.

            Args:
                event_type (`EventListener.EventType`): The type of event to stop listening for.
                listener (Callable): The callback function to remove.

            Returns:
                None
            """
            with self._lock:
                if (
                    event_type in self.listeners
                    and listener in self.listeners[event_type]
                ):
                    self.listeners[event_type].remove(listener)
                    # Cleanup priority and filter data
                    self.listener_priority.pop(event_type, None)
                    self.listener_filter.pop(listener, None)

        def emit_event(self, event_data: "EventListener.EventData") -> None:
            """
            Emits an event to all registered listeners.

            Args:
                event_data (`EventListener.EventData`): The data associated with the event.

            Returns:
                None
            """
            with self._lock:
                listeners = self.listeners.get(event_data.event_type, []).copy()

            for listener in listeners:
                try:
                    # Apply filter if exists
                    filter_func = self.listener_filter.get(listener)
                    if filter_func and not filter_func(event_data):
                        continue

                    # Call the listener
                    listener(event_data)

                except Exception as e:
                    print(f"Error in event listener {listener.__name__}: {e}")

        def emit_async(self, event_data: "EventListener.EventData") -> None:
            """
            Emits an event asynchronously (non-blocking).

            Args:
                event_data (`EventListener.EventData`): The data associated with the event.

            Returns:
                None
            """
            thread = threading.Thread(target=self.emit_event, args=(event_data,))
            thread.daemon = True
            thread.start()


# Global event manager instance
event_manager = EventListener.EventManager()
