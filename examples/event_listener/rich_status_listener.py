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

import time
import threading
from datetime import datetime
from rich.console import Console
from rich.status import Status
from rich.panel import Panel
from rich.table import Table

# Import the event system from same directory
from event_listener import EventListener, event_manager


class RichStatusListener:
    """
    🎯 Purpose: Listen to events and update Rich.status display

    Rich.status shows a spinning indicator with live status updates.
    This class automatically updates the display when:
    - Variables change in event-aware classes
    - Manual status events are emitted
    """

    def __init__(self, console=None):
        """
        Initialize the Rich status listener

        Args:
            console (Console, optional): Rich Console instance. Creates new one if None.
        """
        self.console = console or Console()
        self.current_status = None
        self.status_context = None
        self.processed_events = set()  # Track "read" events (your requirement!)
        self.is_active = False
        self.status_lock = threading.Lock()
        self.event_history = []

        # Register with event system automatically
        self._register_listeners()

        print("🎯 Rich Status Listener initialized!")

    def _register_listeners(self):
        """
        Register this listener with the event system

        This connects our handler functions to the EventManager so they get
        called automatically when events occur.
        """
        # Register for variable changes (medium priority)
        event_manager.register_listener(
            EventListener.EventType.VARIABLE_CHANGED,
            self.on_variable_changed,
            priority=10,
        )

        # Register for status changes (higher priority)
        event_manager.register_listener(
            EventListener.EventType.STATUS_CHANGED,
            self.on_status_changed,
            priority=15,  # Higher priority - status changes are more important
        )

        # Register for error events (highest priority)
        event_manager.register_listener(
            EventListener.EventType.ERROR_OCCURRED,
            self.on_error_occurred,
            priority=20,  # Highest priority - errors are critical
        )

        print("✅ Rich Status Listener registered with event system!")

    def on_variable_changed(self, event_data):
        """
        Handle variable change events - update Rich.status display

        This function is called automatically when any variable changes
        in event-aware classes.

        Args:
            event_data (EventListener.EventData): The event information
        """
        # Create unique event ID for "read" tracking (your requirement!)
        event_id = f"{event_data.source_class.__name__}_{event_data.variable_name}_{event_data.time_stamp}"

        # Skip if already processed (prevents duplicate updates)
        if event_id in self.processed_events:
            return

        # Create status message for variable change
        status_message = f"🔄 {event_data.source_class.__name__}.{event_data.variable_name} = {event_data.new_value}"

        # Update Rich.status display
        self.update_status(status_message)

        # Mark as processed (your "read" requirement!)
        self.processed_events.add(event_id)

        # Add to history for debugging
        self.event_history.append(
            {
                "type": "variable_change",
                "event_id": event_id,
                "timestamp": event_data.time_stamp,
                "message": status_message,
                "data": event_data,
            }
        )

        # Cleanup old events to prevent memory leaks
        self._cleanup_processed_events()

        print(f"📝 Variable change processed: {status_message}")

    def on_status_changed(self, event_data):
        """
        Handle status change events - direct status updates

        This function is called when manual status events are emitted
        using emit_status_event().

        Args:
            event_data (EventListener.EventData): The event information
        """
        # Create status message for status change
        status_message = f"📊 {event_data.new_value}"

        # Update Rich.status display
        self.update_status(status_message)

        # Add to history
        self.event_history.append(
            {
                "type": "status_change",
                "timestamp": event_data.time_stamp,
                "message": status_message,
                "data": event_data,
            }
        )

        print(f"📊 Status change processed: {status_message}")

    def on_error_occurred(self, event_data):
        """
        Handle error events - high priority status updates

        Args:
            event_data (EventListener.EventData): The event information
        """
        # Create error status message
        status_message = f"🚨 ERROR: {event_data.new_value}"

        # Update Rich.status display with error
        self.update_status(status_message)

        # Add to history
        self.event_history.append(
            {
                "type": "error",
                "timestamp": event_data.time_stamp,
                "message": status_message,
                "data": event_data,
            }
        )

        print(f"🚨 Error processed: {status_message}")

    def start_status_display(self, initial_message="🚀 System Ready..."):
        """
        Start the Rich.status display

        This creates the spinning indicator that shows live status updates.

        Args:
            initial_message (str): Initial status message to show
        """
        with self.status_lock:
            if not self.is_active:
                try:
                    # Create Rich.status context manager
                    self.status_context = self.console.status(initial_message)
                    # Enter the context (starts the spinner)
                    self.current_status = self.status_context.__enter__()
                    self.is_active = True
                    print(f"✅ Rich.status started: {initial_message}")
                except Exception as e:
                    print(f"❌ Failed to start Rich.status: {e}")
            else:
                print("⚠️ Rich.status already active")

    def update_status(self, message):
        """
        Update the current status message

        This changes what's displayed in the Rich.status spinner.

        Args:
            message (str): New status message to display
        """
        with self.status_lock:
            if self.is_active and self.current_status:
                try:
                    # Update the Rich.status message
                    self.current_status.update(message)
                    print(f"🔄 Rich.status updated: {message}")
                except Exception as e:
                    print(f"❌ Failed to update Rich.status: {e}")
                    # Fallback to console print
                    self.console.print(f"📊 Status: {message}")
            else:
                # If status not active, just print the message
                self.console.print(f"📊 Status: {message}")

    def stop_status_display(self):
        """
        Stop the Rich.status display

        This stops the spinning indicator and cleans up resources.
        """
        with self.status_lock:
            if self.is_active and self.status_context:
                try:
                    # Exit the context (stops the spinner)
                    self.status_context.__exit__(None, None, None)
                    self.current_status = None
                    self.status_context = None
                    self.is_active = False
                    print("⏹️ Rich.status stopped")
                except Exception as e:
                    print(f"❌ Failed to stop Rich.status: {e}")
            else:
                print("⚠️ Rich.status not active")

    def _cleanup_processed_events(self):
        """
        Clean up old processed events to prevent memory leaks

        Keeps only the most recent events to prevent unlimited memory growth.
        """
        if len(self.processed_events) > 1000:
            # Keep only recent 500 events
            recent_events = list(self.processed_events)[-500:]
            self.processed_events = set(recent_events)
            print("🧹 Cleaned up old processed events")

        # Also cleanup history
        if len(self.event_history) > 100:
            self.event_history = self.event_history[-50:]
            print("🧹 Cleaned up old event history")

    def get_status_info(self):
        """
        Get information about the status system

        Returns:
            dict: Status system information
        """
        return {
            "is_active": self.is_active,
            "processed_events_count": len(self.processed_events),
            "event_history_count": len(self.event_history),
            "current_message": getattr(self.current_status, "_status", "None")
            if self.current_status
            else "None",
        }

    def show_event_statistics(self):
        """
        Display statistics about processed events using Rich formatting
        """
        stats_table = Table(title="📊 Rich Status Event Statistics")
        stats_table.add_column("Metric", style="cyan", no_wrap=True)
        stats_table.add_column("Value", style="green")

        # Basic stats
        stats_table.add_row("Status Active", "✅ Yes" if self.is_active else "❌ No")
        stats_table.add_row("Processed Events", str(len(self.processed_events)))
        stats_table.add_row("Event History", str(len(self.event_history)))

        # Event type breakdown
        event_types = {}
        for event in self.event_history:
            event_type = event["type"]
            event_types[event_type] = event_types.get(event_type, 0) + 1

        for event_type, count in event_types.items():
            stats_table.add_row(f"  {event_type.title()}", str(count))

        # Recent events
        if self.event_history:
            recent_event = self.event_history[-1]
            stats_table.add_row(
                "Last Event",
                recent_event["message"][:50] + "..."
                if len(recent_event["message"]) > 50
                else recent_event["message"],
            )
            stats_table.add_row(
                "Last Event Time",
                datetime.fromtimestamp(recent_event["timestamp"]).strftime("%H:%M:%S"),
            )

        # Display the table
        stats_panel = Panel(
            stats_table, title="Event System Statistics", border_style="yellow"
        )
        self.console.print(stats_panel)


# Global Rich status listener instance
rich_status_listener = RichStatusListener()
