# 🎯 Event-Aware Decorators and Utilities
"""
Event-Aware Decorators for AI-Agent-Workflow Project

This module provides decorators and utilities to make classes automatically
emit events when their attributes change.

Usage:
    from examples.event_decorators import make_class_event_aware, event_aware_property

    # Method 1: Make entire class event-aware
    @make_class_event_aware
    class MyClass:
        def __init__(self):
            self.status = "idle"  # Will automatically emit events

    # Method 2: Make specific properties event-aware
    class MyClass:
        status = event_aware_property()  # Only this property emits events
"""

import time
import sys
import os
from functools import wraps

# Add src/utils to path to import event_listener
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "utils"))
from event_listener import EventListener, event_manager


def event_aware_property(event_type=None):
    """
    Property descriptor that automatically emits events when changed

    This creates a property that automatically emits events whenever
    its value is changed. Use this when you only want specific
    attributes to emit events.

    Args:
        event_type (EventListener.EventType, optional): Type of event to emit.
            Defaults to VARIABLE_CHANGED.

    Returns:
        Property descriptor that emits events on change

    Example:
        class DataProcessor:
            status = event_aware_property()  # Emits events when status changes
            progress = event_aware_property()  # Emits events when progress changes

            def __init__(self):
                self.status = "idle"  # Will emit event
                self.progress = 0     # Will emit event
    """
    if event_type is None:
        event_type = EventListener.EventType.VARIABLE_CHANGED

    class EventAwareDescriptor:
        def __init__(self):
            self.value = None
            self.name = None

        def __set_name__(self, owner, name):
            """Called when the descriptor is assigned to a class attribute"""
            self.name = name

        def __get__(self, obj, objtype=None):
            """Called when the attribute is accessed (reading)"""
            if obj is None:
                return self
            # Get value from instance's private attribute
            return getattr(obj, f"_{self.name}", self.value)

        def __set__(self, obj, value):
            """
            Called when the attribute is set (writing)

            This is where the event emission happens automatically.
            """
            # Get the old value
            old_value = getattr(obj, f"_{self.name}", self.value)

            # Set the new value in private attribute
            setattr(obj, f"_{self.name}", value)

            # Emit event if value actually changed
            if old_value != value:
                event_data = EventListener.EventData(
                    event_type=event_type,
                    source_class=obj.__class__,
                    variable_name=self.name,
                    old_value=old_value,
                    new_value=value,
                    time_stamp=time.time(),
                    meta_data={"change_method": "property_descriptor"},
                )

                # Emit the event through your global event manager
                event_manager.emit_event(event_data)

    return EventAwareDescriptor()


def make_class_event_aware(cls):
    """
    Class decorator that makes ALL attribute changes emit events

    This modifies the class's __setattr__ method to automatically
    emit events whenever ANY attribute is changed. Use this when
    you want all attribute changes to be tracked.

    Args:
        cls: The class to make event-aware

    Returns:
        The modified class with event emission capabilities

    Example:
        @make_class_event_aware
        class DataProcessor:
            def __init__(self):
                self.status = "idle"    # Will emit event
                self.progress = 0       # Will emit event
                self.error_count = 0    # Will emit event

        processor = DataProcessor()
        processor.status = "processing"  # Will emit event automatically!
    """
    # Store the original __setattr__ method
    original_setattr = cls.__setattr__

    def event_aware_setattr(self, name, value):
        """
        Replacement __setattr__ that emits events

        This method is called every time an attribute is set on the class.
        We intercept it to emit events when values change.
        """
        # Skip private attributes, methods, and special attributes
        if (
            name.startswith("_")
            or callable(value)
            or name in ["__dict__", "__weakref__"]
        ):
            original_setattr(self, name, value)
            return

        # Get old value before changing
        old_value = getattr(self, name, None) if hasattr(self, name) else None

        # Set new value using original method
        original_setattr(self, name, value)

        # Emit event if value actually changed
        if old_value != value:
            event_data = EventListener.EventData(
                event_type=EventListener.EventType.VARIABLE_CHANGED,
                source_class=self.__class__,
                variable_name=name,
                old_value=old_value,
                new_value=value,
                time_stamp=time.time(),
                meta_data={"change_method": "setattr_override"},
            )

            # Emit the event
            event_manager.emit_event(event_data)

    # Replace the class's __setattr__ method
    cls.__setattr__ = event_aware_setattr

    # Add a flag to indicate this class is event-aware
    cls._is_event_aware = True

    return cls


def event_emitter(event_type, variable_name=None):
    """
    Method decorator that emits events when the decorated method is called

    Use this to emit events when specific methods are called, especially
    setter methods or methods that change important state.

    Args:
        event_type (EventListener.EventType): Type of event to emit
        variable_name (str, optional): Name of the variable being changed.
            If None, uses the method name.

    Returns:
        Decorated method that emits events when called

    Example:
        class DataProcessor:
            def __init__(self):
                self.processing_state = "idle"

            @event_emitter(EventListener.EventType.VARIABLE_CHANGED, "processing_state")
            def set_processing_state(self, new_state):
                old_state = self.processing_state
                self.processing_state = new_state
                return old_state  # Can return old value for event
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Get variable name (use provided name or method name)
            var_name = variable_name or func.__name__

            # Get old value if the attribute exists
            old_value = (
                getattr(self, var_name, None) if hasattr(self, var_name) else None
            )

            # Execute the original method
            result = func(self, *args, **kwargs)

            # Get new value after method execution
            new_value = (
                getattr(self, var_name, None)
                if hasattr(self, var_name)
                else (args[0] if args else None)
            )

            # Emit event if value changed
            if old_value != new_value:
                event_data = EventListener.EventData(
                    event_type=event_type,
                    source_class=self.__class__,
                    variable_name=var_name,
                    old_value=old_value,
                    new_value=new_value,
                    time_stamp=time.time(),
                    meta_data={
                        "change_method": "method_decorator",
                        "method_name": func.__name__,
                        "args": str(args)[:100],  # Truncate long args
                        "kwargs": str(kwargs)[:100],  # Truncate long kwargs
                    },
                )
                event_manager.emit_event(event_data)

            return result

        return wrapper

    return decorator


class EventAwareBase:
    """
    Base class that provides event-aware functionality

    Inherit from this class to automatically get event emission
    capabilities without using decorators.

    Example:
        class DataProcessor(EventAwareBase):
            def __init__(self):
                super().__init__()
                self.status = "idle"  # Will emit event
                self.progress = 0     # Will emit event
    """

    def __init__(self):
        """Initialize the event-aware base class"""
        # Flag to prevent events during initialization
        self._initializing = True
        super().__init__()
        self._initializing = False

    def __setattr__(self, name, value):
        """Override setattr to emit events"""
        # Skip during initialization and for private attributes
        if (
            getattr(self, "_initializing", True)
            or name.startswith("_")
            or callable(value)
        ):
            super().__setattr__(name, value)
            return

        # Get old value
        old_value = getattr(self, name, None) if hasattr(self, name) else None

        # Set new value
        super().__setattr__(name, value)

        # Emit event if changed
        if old_value != value:
            event_data = EventListener.EventData(
                event_type=EventListener.EventType.VARIABLE_CHANGED,
                source_class=self.__class__,
                variable_name=name,
                old_value=old_value,
                new_value=value,
                time_stamp=time.time(),
                meta_data={"change_method": "base_class"},
            )
            event_manager.emit_event(event_data)

    def emit_status(self, message, metadata=None):
        """
        Convenience method to emit status events

        Args:
            message (str): Status message
            metadata (dict, optional): Additional metadata
        """
        from examples.event_helpers import emit_status_event

        emit_status_event(self.__class__, message, metadata)

    def emit_error(self, error_message, var_name="error", metadata=None):
        """
        Convenience method to emit error events

        Args:
            error_message (str): Error message
            var_name (str): Variable name associated with error
            metadata (dict, optional): Additional metadata
        """
        from examples.event_helpers import emit_error_event

        emit_error_event(self.__class__, error_message, var_name, metadata)


def selective_event_aware(*attribute_names):
    """
    Class decorator that makes only specific attributes emit events

    Use this when you want fine-grained control over which attributes
    emit events, without using property descriptors.

    Args:
        *attribute_names: Names of attributes that should emit events

    Returns:
        Class decorator function

    Example:
        @selective_event_aware('status', 'progress', 'error_count')
        class DataProcessor:
            def __init__(self):
                self.status = "idle"        # Will emit events
                self.progress = 0           # Will emit events
                self.error_count = 0        # Will emit events
                self.internal_data = {}     # Will NOT emit events
    """

    def decorator(cls):
        # Store original __setattr__
        original_setattr = cls.__setattr__

        def selective_setattr(self, name, value):
            """Only emit events for specified attributes"""
            # Get old value
            old_value = getattr(self, name, None) if hasattr(self, name) else None

            # Set new value
            original_setattr(self, name, value)

            # Emit event only if this attribute is in the watch list
            if (
                name in attribute_names
                and old_value != value
                and not name.startswith("_")
            ):
                event_data = EventListener.EventData(
                    event_type=EventListener.EventType.VARIABLE_CHANGED,
                    source_class=self.__class__,
                    variable_name=name,
                    old_value=old_value,
                    new_value=value,
                    time_stamp=time.time(),
                    meta_data={"change_method": "selective_event_aware"},
                )
                event_manager.emit_event(event_data)

        # Replace __setattr__
        cls.__setattr__ = selective_setattr
        cls._watched_attributes = attribute_names

        return cls

    return decorator


# Utility functions
def is_event_aware(obj_or_class):
    """
    Check if an object or class is event-aware

    Args:
        obj_or_class: Object instance or class to check

    Returns:
        bool: True if event-aware, False otherwise
    """
    if hasattr(obj_or_class, "__class__"):
        # It's an instance
        cls = obj_or_class.__class__
    else:
        # It's a class
        cls = obj_or_class

    return (
        hasattr(cls, "_is_event_aware")
        or issubclass(cls, EventAwareBase)
        or hasattr(cls, "_watched_attributes")
    )


def get_watched_attributes(obj_or_class):
    """
    Get list of attributes that emit events for an event-aware class

    Args:
        obj_or_class: Object instance or class to check

    Returns:
        list: List of attribute names that emit events, or None if not event-aware
    """
    if hasattr(obj_or_class, "__class__"):
        cls = obj_or_class.__class__
    else:
        cls = obj_or_class

    if hasattr(cls, "_watched_attributes"):
        return list(cls._watched_attributes)
    elif hasattr(cls, "_is_event_aware"):
        return "all_attributes"  # All attributes are watched
    else:
        return None
