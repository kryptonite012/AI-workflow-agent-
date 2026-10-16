# 🎯 Rich Status Event Listener System
"""
Rich Status Event Listener for Event System Examples

This module provides Rich.status integration with the event system.
It automatically updates Rich.status display when variables change or status events occur.

Usage:
    from rich_status_listener import rich_status_listener

    # Start Rich.status display
    rich_status_listener.start_status_display("🚀 System initializing...")

    # Your event-aware classes will automatically update the status
"""

import sys
import threading
from typing import Optional, List
from weakref import WeakKeyDictionary

from rich.console import Console
from rich.status import Status

from src.ui.diagnostics.debug_helpers import debug_info
from src.utils.listeners.event_listener import EventListener


class RichStatusListener:
    """
    🎯 Purpose: Listen to events and update Rich.status display

    Rich.status shows a spinning indicator with live status updates.
    This class automatically updates the display when:
    - Variables change in event-aware classes
    - Manual status events are emitted
    """

    _listeners = WeakKeyDictionary()  # WeakKeyDictionary to hold listeners so when ever new listener is created added to the dictionary
    event_manager: EventListener.EventManager = (
        None  # This will be initialized in the __init__ method
    )

    class ConsoleDescriptor:
        """
        🎯 Descriptor for Console validation

        Ensures that only Rich Console instances can be assigned to the console attribute.
        Uses WeakKeyDictionary to prevent memory leaks.
        """

        def __init__(self):
            self.instance_data = WeakKeyDictionary()

        def __get__(self, instance, owner):
            if instance is None:
                return self
            return self.instance_data.get(instance, None)

        def __set__(self, instance, value):
            # ✅ CORRECT: Validate the VALUE being assigned, not the instance
            if not isinstance(value, Console):
                raise TypeError(
                    f"console must be a Rich Console instance, got {type(value).__name__}"
                )

            # Store the console for this specific RichStatusListener instance
            self.instance_data[instance] = value

        def __delete__(self, instance):
            if instance in self.instance_data:
                del self.instance_data[instance]

    class StatusContextDescriptor:
        """
        🎯 Descriptor for Status Context validation

        Ensures that only Rich Status context managers can be assigned.
        """

        def __init__(self):
            self.instance_data = WeakKeyDictionary()

        def __get__(self, instance, owner):
            if instance is None:
                return self
            return self.instance_data.get(instance, None)

        def __set__(self, instance, value):
            # ✅ CORRECT: Validate status context (can be None or have __enter__/__exit__)
            if value is not None:
                if not (hasattr(value, "__enter__") and hasattr(value, "__exit__")):
                    raise TypeError(
                        f"status_context must be a context manager (have __enter__ and __exit__), got {type(value).__name__}"
                    )

            self.instance_data[instance] = value

        def __delete__(self, instance):
            if instance in self.instance_data:
                del self.instance_data[instance]

    # ✅ Assign descriptors to class attributes
    console = ConsoleDescriptor()
    status_context = StatusContextDescriptor()

    def __repr__(self):
        """
        Full string representation of the RichStatusListener instance.
        Includes instance name (if available), console variable name, status_context, and id.
        """
        # Try to get the variable name of the instance if possible (best effort)
        import inspect

        name = None
        for frame_info in inspect.stack():
            frame = frame_info.frame
            for var_name, var_val in frame.f_locals.items():
                if var_val is self:
                    name = var_name
                    break
            if name:
                break

        # Try to get the variable name of the console if possible (best effort)
        console_name = None
        for frame_info in inspect.stack():
            frame = frame_info.frame
            for var_name, var_val in frame.f_locals.items():
                if var_val is self.console:
                    console_name = var_name
                    break
            if console_name:
                break

        return (
            f"<RichStatusListener name={name!r} id={id(self)} "
            f"console=({console_name!r}, id={id(self.console)}) "
            f"status_context={self.status_context}>"
        )

    def __init__(self, console=None, status_context=None):
        """
        Initialize the Rich status listener with proper validation

        Args:
            console (Console, optional): Rich Console instance. Creates new one if None.
            status_context (optional): Status context manager. Will be created when needed if None.
        """

        # Add this instance to the listeners dictionary if it is not already present, ensuring each listener is isolated and managed independently
        if self not in RichStatusListener._listeners:
            RichStatusListener._listeners[self] = self
        else:
            raise ValueError(
                "This RichStatusListener instance already exists. Use a new instance."
            )

        # ✅ PROPER DESCRIPTOR USAGE: Assignment triggers validation
        if console is None:
            console = Console()

        # These assignments will trigger the descriptor validation
        self.console = (
            console  # ← ConsoleDescriptor.__set__ validates this is a Console
        )
        self.status_context: Status = status_context  # ← StatusContextDescriptor.__set__ validates this is a context manager or None
        self.current_status = None  # this is the __enter__ of the status context manager it is equivalent to status.start()
        self.status_thread_lock = threading.Lock()
        self.processed_events = set()
        self.status_is_active = False
        self.event_history: List[EventListener.EventData] = []
        RichStatusListener.event_manager = EventListener.EventManager()

        # Register with event system automatically
        self._register_variable_listener()
        debug_info(
            heading="RICH_STATUS_LISTENER • INIT",
            body="🎯 Rich Status Listener initialized!",
            metadata={"listener_id": id(self)},
        )

    def _do_we_need_to_listen(self, event_data):
        """
        Checks whether the listener should actively listen for events and update the Rich status display.

        Returns:
            bool: True if the listener should listen, False otherwise.
        """
        # Check if the event data contains metadata of id for this listener
        if not event_data.meta_data:
            return False
        if "id" in event_data.meta_data and event_data.meta_data["id"] == id(self):
            return True
        return False

    def _register_variable_listener(self):
        """
        Registers a listener for variable changes.
        :return:
        """
        from src.utils.listeners.event_listener import EventListener

        self.event_manager.register_listener(
            EventListener.EventType.VARIABLE_CHANGED,
            self._on_variable_changed,
            filter_func=self._do_we_need_to_listen,
            # this is the function that decides whether the listener should listen or not
            priority=5,
        )

    def _on_variable_changed(self, event_data):
        """
        Handles status change events and updates the rich status display accordingly.

        Args:
            event_data (EventListener.EventData): Contains detailed information about the status change event.
                - source_class (type): The originating class of the event.
                - variable_name (str, optional): The name of the variable that changed.
                - old_value (Any, optional): The previous value before the change.
                - new_value (Any, optional): The updated value after the change.
                - time_stamp (float, optional): The time the event occurred.
                - meta_data (Dict[str, Any], optional): Additional contextual metadata for the event.
            ** Make sure to use the locks for changing the status
        """

        meta_data = event_data.meta_data

        event_info = f"{event_data.source_class.__name__ if not isinstance(event_data.source_class, str) else event_data.source_class} - {event_data.event_type} changed from {meta_data['old_value']} to {meta_data['new_value']}"
        if event_info in self.processed_events:
            return

        # new status message
        status_message = f"{event_data.meta_data.get('new_value', 'Unknown')}"

        self._update_status(status_message)

        self.processed_events.add(event_info)

        # append in history for debugging

        self.event_history.append(event_data)
        self._clean_up_processed_events()

        # here the variable change is happened

    def _update_status(self, status_message):
        """
        Updates the rich status in the console.
        If a status context is provided, it will be used to update the status.
        Otherwise, it will directly update the console.

        Args:
            status_message (str): The message to display as the current status.
        """
        # this is the threatening code because it makes the status if the status got closed we actually
        # have to start manually the status context manager because it is the safest way to check whether
        # status is existed or not
        # update is the function of the status actual context manager
        with self.status_thread_lock:
            if self.status_is_active and self.current_status:
                self.current_status.update(status_message)
            else:
                debug_info(
                    heading="RICH_STATUS_LISTENER • STATUS_UPDATE",
                    body=f"Status context is not active, cannot update status. {status_message}",
                    metadata={"listener_id": id(self)},
                )

    def start_status(self, initial_message, spinner="dots"):
        """
        Starts the rich status context manager with the given message.

        Args:
            initial_message (str): The initial message to display in the status.
            spinner (str): The spinner type to use for the status display. Defaults to "dots".
        """

        with self.status_thread_lock:
            if not self.status_is_active:
                self.status_context = self.console.status(
                    initial_message, spinner=spinner
                )  # the status is now set to the context manager
                self.current_status = self.status_context.__enter__()
                self.status_is_active = True
                debug_info(
                    heading="RICH_STATUS_LISTENER • STATUS_START",
                    body=f"Status started with message: {initial_message}",
                    metadata={"listener_id": id(self)},
                )
                # save the first status message in the processed events
                start_event = EventListener.EventData(
                    event_type=EventListener.EventType.VARIABLE_CHANGED,
                    source_class=self.__class__,
                    meta_data={
                        "id": id(self),
                        "old_value": None,
                        "new_value": initial_message,
                        "variable_name": "status",
                    },
                )
                self.event_history.append(start_event)
            else:
                debug_info(
                    heading="RICH_STATUS_LISTENER • STATUS_START",
                    body=f"Status is already active of consol object {self.console}, cannot start again.",
                    metadata={"listener_id": id(self)},
                )

    def stop_status_display(self):
        """
        Stops the rich status context manager if it is active.
        """
        with self.status_thread_lock:
            if self.status_is_active and self.current_status:
                self.current_status.__exit__(None, None, None)
                # Clean up the current status
                self.current_status = None
                self.status_context = None
                self.event_manager.unregister_listener(
                    EventListener.EventType.VARIABLE_CHANGED, self._on_variable_changed
                )
                # Set the status to inactive

                self.status_is_active = False
                RichStatusListener._listeners.pop(
                    self
                )  # Remove this listener from the listeners dictionary
                debug_info(
                    heading="RICH_STATUS_LISTENER • STATUS_STOP",
                    body=f"RichStatusListener refcount: {sys.getrefcount(RichStatusListener)}",
                    metadata={"listener_id": id(self)},
                )
            else:
                debug_info(
                    heading="RICH_STATUS_LISTENER • STATUS_STOP",
                    body=f"Status is not active, cannot stop. of console object {self.console}",
                    metadata={"listener_id": id(self)},
                )

    def _clean_up_processed_events(self):
        """
        Cleans up the processed events to prevent memory leaks.
        This function removes events that are older than a certain threshold.
        """
        # For simplicity, we can just clear the processed events after a certain number of events
        if len(self.processed_events) > 1000:
            self.processed_events = set(
                list(self.processed_events)[-1000:]
            )  # Keep the last 1000 events
            debug_info(
                heading="RICH_STATUS_LISTENER • CLEANUP",
                body="Processed events cleared to prevent memory leaks.",
                metadata={"listener_id": id(self)},
            )

        if len(self.event_history) > 1000:
            self.event_history = self.event_history[-1000:]
            debug_info(
                heading="RICH_STATUS_LISTENER • CLEANUP",
                body="Event history cleared to prevent memory leaks.",
                metadata={"listener_id": id(self)},
            )

    def get_last_event(self) -> Optional[EventListener.EventData]:
        """
        Returns the last event from the event history.

        Returns:
            dict: The last event data or None if no events are recorded.
        """
        if self.event_history:
            return self.event_history[-1]
        return None

    def emit_on_variable_change(
            self, source_class, variable_name, old_value, new_value
    ):
        """
        Emits a variable change event to update the status display.
        this is limited to the variable change event only, because this is the only event that we are interested in for
        changing the status display.

        Args:
            source_class (type): The class where the variable change occurred.
            variable_name (str): The name of the variable that changed.
            old_value (Any): The previous value of the variable.
            new_value (Any): The updated value of the variable.
        """
        from src.utils.listeners.event_listener import EventListener

        event_data = EventListener.EventData(
            event_type=EventListener.EventType.VARIABLE_CHANGED,
            source_class=source_class,
            meta_data={
                "id": id(self),
                "old_value": old_value,
                "new_value": new_value,
                "variable_name": variable_name,
            },
        )
        EventListener.EventManager().emit_event(event_data)

    def unregister_n_stop(self):
        """
        Unregisters this listener from the event system and cleans up resources.
        """
        with self.status_thread_lock:
            if self in RichStatusListener._listeners:
                self.event_manager.unregister_listener(
                    EventListener.EventType.VARIABLE_CHANGED, self._on_variable_changed
                )
                RichStatusListener._listeners.pop(self, None)
                debug_info(
                    heading="RICH_STATUS_LISTENER • UNREGISTER",
                    body=f"Unregistered {self} from RichStatusListener.",
                    metadata={"listener_id": id(self)},
                )
            else:
                debug_info(
                    heading="RICH_STATUS_LISTENER • UNREGISTER",
                    body=f"{self} was not registered in RichStatusListener.",
                    metadata={"listener_id": id(self)},
                )
            self.stop_status_display()
