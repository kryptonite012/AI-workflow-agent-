# 🎯 Event Helper Functions
"""
Event Helper Functions for Event System Examples

This module provides convenient functions for manually emitting events.
Use these when you want to trigger Rich.status updates manually.

Usage:
    from event_helpers import emit_status_event, emit_variable_event, emit_error_event

    # Emit a status change
    emit_status_event(MyClass, "Processing started...")

    # Emit a variable change
    emit_variable_event(MyClass, "progress", 50, 75)

    # Emit an error
    emit_error_event(MyClass, "Connection failed")
"""

import time
from event_listener import EventListener, event_manager


def emit_status_event(source_class, message, metadata=None):
    """
    Manually emit a status change event

    This will trigger Rich.status updates with user-friendly messages.
    Use this for high-level status updates like "Processing started", "Completed", etc.

    Args:
        source_class: The class that's changing status (can be class or instance)
        message (str): The status message to display
        metadata (dict, optional): Additional data to include with the event

    Example:
        emit_status_event(FileProcessor, "📁 Starting file processing...")
        emit_status_event(self.__class__, "✅ Processing completed!")
    """
    # Handle both class and instance
    if hasattr(source_class, "__class__"):
        # It's an instance, get the class
        actual_class = source_class.__class__
    else:
        # It's already a class
        actual_class = source_class

    # Create event data
    event_data = EventListener.EventData(
        event_type=EventListener.EventType.STATUS_CHANGED,
        source_class=actual_class,
        variable_name="status",
        old_value=None,
        new_value=message,
        time_stamp=time.time(),
        meta_data=metadata or {},
    )

    # Emit the event
    event_manager.emit_event(event_data)
    print(f"📤 Status event emitted: {message}")


def emit_variable_event(source_class, var_name, old_val, new_val, metadata=None):
    """
    Manually emit a variable change event

    This will trigger Rich.status updates showing specific variable changes.
    Use this when you want to manually notify about variable changes.

    Args:
        source_class: The class where variable changed (can be class or instance)
        var_name (str): Name of the variable that changed
        old_val: Previous value of the variable
        new_val: New value of the variable
        metadata (dict, optional): Additional data to include with the event

    Example:
        emit_variable_event(DataProcessor, "progress", 50, 75)
        emit_variable_event(self.__class__, "connection_count", 5, 6)
    """
    # Handle both class and instance
    if hasattr(source_class, "__class__"):
        # It's an instance, get the class
        actual_class = source_class.__class__
    else:
        # It's already a class
        actual_class = source_class

    # Create event data
    event_data = EventListener.EventData(
        event_type=EventListener.EventType.VARIABLE_CHANGED,
        source_class=actual_class,
        variable_name=var_name,
        old_value=old_val,
        new_value=new_val,
        time_stamp=time.time(),
        meta_data=metadata or {"manual_emission": True},
    )

    # Emit the event
    event_manager.emit_event(event_data)
    print(f"📤 Variable event emitted: {var_name} = {new_val}")


def emit_error_event(source_class, error_message, var_name="error", metadata=None):
    """
    Manually emit an error event

    This will trigger Rich.status updates with error messages (highest priority).
    Use this when errors occur that should be immediately visible.

    Args:
        source_class: The class where error occurred (can be class or instance)
        error_message (str): The error message to display
        var_name (str, optional): Variable name associated with error. Defaults to "error".
        metadata (dict, optional): Additional data to include with the event

    Example:
        emit_error_event(DatabaseManager, "Connection timeout")
        emit_error_event(self.__class__, "File not found", "file_path")
    """
    # Handle both class and instance
    if hasattr(source_class, "__class__"):
        # It's an instance, get the class
        actual_class = source_class.__class__
    else:
        # It's already a class
        actual_class = source_class

    # Create event data
    event_data = EventListener.EventData(
        event_type=EventListener.EventType.ERROR_OCCURRED,
        source_class=actual_class,
        variable_name=var_name,
        old_value=None,
        new_value=error_message,
        time_stamp=time.time(),
        meta_data=metadata or {"manual_emission": True},
    )

    # Emit the event
    event_manager.emit_event(event_data)
    print(f"📤 Error event emitted: {error_message}")


# Convenience functions for common patterns
def start_operation_status(source_class, operation_name):
    """
    Convenience function to emit 'operation started' status

    Args:
        source_class: The class starting the operation
        operation_name (str): Name of the operation
    """
    emit_status_event(source_class, f"🚀 {operation_name} started...")


def complete_operation_status(source_class, operation_name):
    """
    Convenience function to emit 'operation completed' status

    Args:
        source_class: The class completing the operation
        operation_name (str): Name of the operation
    """
    emit_status_event(source_class, f"✅ {operation_name} completed!")


def progress_update(source_class, current, total, operation_name="Processing"):
    """
    Convenience function to emit progress updates

    Args:
        source_class: The class reporting progress
        current (int): Current progress value
        total (int): Total progress value
        operation_name (str): Name of the operation
    """
    percentage = int((current / total) * 100) if total > 0 else 0
    emit_variable_event(
        source_class, "progress", current - 1 if current > 0 else 0, current
    )
    emit_status_event(
        source_class, f"📊 {operation_name}: {percentage}% ({current}/{total})"
    )
