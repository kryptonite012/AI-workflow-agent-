# 🧪 Simple Event Listener Example
"""
Simple, minimal example of the event listener system

This file demonstrates the core concepts without Rich.status complexity.
Perfect for understanding the basic event system mechanics.

Usage:
    python event_listener.py
"""

import time
import sys
import os

# Add parent directory to path to import the main event system
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import from parent directory to avoid naming conflict
import importlib.util

spec = importlib.util.spec_from_file_location(
    "main_event_listener", os.path.join(parent_dir, "event_listener.py")
)
main_event_listener = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_event_listener)

EventListener = main_event_listener.EventListener
event_manager = main_event_listener.event_manager


def simple_listener(event_data):
    """Simple event listener that just prints events"""
    print(
        f"📨 Event: {event_data.source_class.__name__}.{event_data.variable_name} = {event_data.new_value}"
    )


def status_listener(event_data):
    """Simple status listener"""
    print(f"📊 Status: {event_data.new_value}")


class SimpleClass:
    """Simple class that manually emits events"""

    def __init__(self, name):
        self.name = name
        self._value = 0

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        old_value = self._value
        self._value = new_value

        # Manually emit event when value changes
        if old_value != new_value:
            event_data = EventListener.EventData(
                event_type=EventListener.EventType.VARIABLE_CHANGED,
                source_class=self.__class__,
                variable_name="value",
                old_value=old_value,
                new_value=new_value,
                time_stamp=time.time(),
            )
            event_manager.emit_event(event_data)

    def set_status(self, status_message):
        """Manually emit status event"""
        event_data = EventListener.EventData(
            event_type=EventListener.EventType.STATUS_CHANGED,
            source_class=self.__class__,
            variable_name="status",
            old_value=None,
            new_value=status_message,
            time_stamp=time.time(),
        )
        event_manager.emit_event(event_data)


def main():
    """Simple demonstration"""
    print("🧪 Simple Event Listener Demo")
    print("=" * 40)

    # Register listeners
    event_manager.register_listener(
        EventListener.EventType.VARIABLE_CHANGED, simple_listener
    )

    event_manager.register_listener(
        EventListener.EventType.STATUS_CHANGED, status_listener
    )

    print("✅ Listeners registered")

    # Create test object
    obj = SimpleClass("TestObject")

    # Test variable changes
    print("\n🧪 Testing variable changes:")
    for i in range(5):
        obj.value = i  # This will emit events automatically!
        time.sleep(0.3)

    # Test status updates
    print("\n🧪 Testing status updates:")
    obj.set_status("Processing started...")
    time.sleep(0.5)
    obj.set_status("Processing completed!")

    print("\n✅ Simple demo completed!")


if __name__ == "__main__":
    main()
