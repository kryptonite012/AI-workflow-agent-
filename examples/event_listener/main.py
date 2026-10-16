# 🎯 Event Listener System - Main Demo
"""
Main demonstration of the Event Listener System with Rich.status integration

This is the main file that demonstrates all features of the event system:
- Automatic variable change detection
- Rich.status updates
- Manual event emission
- Event-aware classes

Usage:
    python main.py          # Full demo
    python main.py quick    # Quick test
"""

import time
import sys
import os

# Import our event system components
from event_listener import EventListener, event_manager
from rich_status_listener import rich_status_listener
from event_helpers import (
    emit_status_event,
    emit_variable_event,
    emit_error_event,
    progress_update,
)

# Rich imports
from rich.console import Console


class SimpleEventAwareClass:
    """
    Example of a manually event-aware class

    This class demonstrates how to make any class emit events
    when its properties change, without using decorators.
    """

    def __init__(self, name):
        self.name = name
        self._status = "idle"
        self._progress = 0
        self._error_count = 0

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        old_value = self._status
        self._status = value

        if old_value != value:
            event_data = EventListener.EventData(
                event_type=EventListener.EventType.VARIABLE_CHANGED,
                source_class=self.__class__,
                variable_name="status",
                old_value=old_value,
                new_value=value,
                time_stamp=time.time(),
            )
            event_manager.emit_event(event_data)

    @property
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, value):
        old_value = self._progress
        self._progress = value

        if old_value != value:
            event_data = EventListener.EventData(
                event_type=EventListener.EventType.VARIABLE_CHANGED,
                source_class=self.__class__,
                variable_name="progress",
                old_value=old_value,
                new_value=value,
                time_stamp=time.time(),
            )
            event_manager.emit_event(event_data)

    @property
    def error_count(self):
        return self._error_count

    @error_count.setter
    def error_count(self, value):
        old_value = self._error_count
        self._error_count = value

        if old_value != value:
            event_data = EventListener.EventData(
                event_type=EventListener.EventType.VARIABLE_CHANGED,
                source_class=self.__class__,
                variable_name="error_count",
                old_value=old_value,
                new_value=value,
                time_stamp=time.time(),
            )
            event_manager.emit_event(event_data)

    def emit_status(self, message):
        """Manually emit status event"""
        emit_status_event(self.__class__, message)

    def emit_error(self, error_message):
        """Manually emit error event"""
        emit_error_event(self.__class__, error_message)


class FileProcessor(SimpleEventAwareClass):
    """
    Example file processor that demonstrates event-driven Rich.status updates
    """

    def __init__(self):
        super().__init__("FileProcessor")
        self.files_processed = 0
        self.current_file = None

    def process_files(self, file_list):
        """Process files with automatic Rich.status updates"""
        self.emit_status("🚀 Starting file processing...")

        self.status = "processing"  # 🎯 Automatically updates Rich.status!

        for i, filename in enumerate(file_list):
            # Update current file
            old_file = self.current_file
            self.current_file = filename

            # Emit manual variable event for current_file
            emit_variable_event(self.__class__, "current_file", old_file, filename)

            # Simulate processing time
            time.sleep(0.5)

            # Update progress
            self.progress = int(
                (i + 1) / len(file_list) * 100
            )  # 🎯 Automatically updates Rich.status!

            # Update files processed count
            self.files_processed = i + 1  # This would need a property to auto-emit
            emit_variable_event(self.__class__, "files_processed", i, i + 1)

            # Simulate occasional errors
            if "error" in filename.lower():
                self.error_count += 1  # 🎯 Automatically updates Rich.status!
                self.emit_error(f"Failed to process {filename}")

            # Progress update with helper function
            progress_update(self.__class__, i + 1, len(file_list), "File Processing")

        self.status = "completed"  # 🎯 Automatically updates Rich.status!
        self.emit_status("✅ File processing completed successfully!")


class DatabaseManager(SimpleEventAwareClass):
    """
    Example database manager with event-driven status updates
    """

    def __init__(self):
        super().__init__("DatabaseManager")
        self.connection_count = 0
        self.query_time = 0.0
        self.last_query = None

    def connect(self):
        """Simulate database connection"""
        self.emit_status("🔌 Connecting to database...")
        time.sleep(0.3)  # Simulate connection time

        # Update connection count (manual emission since no property)
        old_count = self.connection_count
        self.connection_count += 1
        emit_variable_event(
            self.__class__, "connection_count", old_count, self.connection_count
        )

        self.emit_status(f"✅ Connected! Total connections: {self.connection_count}")

    def execute_query(self, query):
        """Simulate query execution"""
        self.emit_status(f"🔍 Executing query: {query[:30]}...")

        # Simulate query execution
        start_time = time.time()
        time.sleep(0.2)  # Simulate query time
        end_time = time.time()

        # Update query time and last query
        old_time = self.query_time
        self.query_time = end_time - start_time
        emit_variable_event(self.__class__, "query_time", old_time, self.query_time)

        old_query = self.last_query
        self.last_query = query
        emit_variable_event(self.__class__, "last_query", old_query, query)

        self.emit_status(f"✅ Query completed in {self.query_time:.3f}s")


def full_demo():
    """
    Complete demonstration of the Event Listener System
    """
    console = Console()

    console.print("🎯 [bold blue]Event Listener System - Full Demo[/bold blue]")
    console.print("=" * 50)

    # Start Rich.status display
    rich_status_listener.start_status_display("🚀 Demo starting...")

    try:
        # Demo 1: File Processing
        console.print("\n📁 [bold green]Demo 1: File Processing[/bold green]")
        processor = FileProcessor()

        file_list = [
            "document1.pdf",
            "image1.jpg",
            "error_file.txt",  # This will trigger an error
            "document2.pdf",
            "image2.png",
        ]

        processor.process_files(file_list)

        time.sleep(2)  # Pause between demos

        # Demo 2: Database Operations
        console.print("\n🗄️ [bold green]Demo 2: Database Operations[/bold green]")
        db_manager = DatabaseManager()

        db_manager.connect()
        db_manager.execute_query("SELECT * FROM users WHERE active = 1")
        db_manager.execute_query("UPDATE users SET last_login = NOW()")
        db_manager.connect()  # Another connection

        time.sleep(2)  # Pause between demos

        # Demo 3: Manual Event Testing
        console.print("\n🧪 [bold green]Demo 3: Manual Event Testing[/bold green]")

        # Test manual events
        emit_status_event("ManualTest", "🧪 Testing manual events...")
        emit_variable_event("ManualTest", "test_var", "old_value", "new_value")
        emit_error_event("ManualTest", "This is a test error")

        time.sleep(2)

        # Show statistics
        console.print("\n📊 [bold yellow]Event System Statistics:[/bold yellow]")
        rich_status_listener.show_event_statistics()

        # Final status
        emit_status_event("DemoSystem", "🎉 Full demo completed successfully!")

        time.sleep(3)  # Let user see final status

    except KeyboardInterrupt:
        console.print("\n⏹️ Demo interrupted by user")
        emit_status_event("DemoSystem", "⏹️ Demo stopped by user")

    except Exception as e:
        console.print(f"\n❌ Demo error: {e}")
        emit_error_event("DemoSystem", f"Demo failed: {str(e)}")

    finally:
        # Stop Rich.status display
        time.sleep(1)
        rich_status_listener.stop_status_display()

        console.print("\n🎯 [bold blue]Demo completed![/bold blue]")
        console.print("=" * 50)

        # Show final statistics
        info = rich_status_listener.get_status_info()
        console.print(f"📊 Final Stats: {info}")


def quick_demo():
    """
    Quick demo for testing
    """
    console = Console()
    console.print("🚀 [bold blue]Quick Event System Demo[/bold blue]")

    # Start status
    rich_status_listener.start_status_display("🧪 Quick test...")

    # Create a simple event-aware class
    test_obj = SimpleEventAwareClass("QuickTest")

    # Test automatic event emission
    for i in range(5):
        test_obj.status = f"step_{i}"  # Should update Rich.status
        test_obj.progress = i * 20  # Should update Rich.status
        if i == 2:
            test_obj.error_count = 1  # Should update Rich.status
        time.sleep(0.5)

    test_obj.emit_status("✅ Quick test completed!")
    time.sleep(2)

    # Stop status
    rich_status_listener.stop_status_display()
    console.print("✅ [bold green]Quick demo completed![/bold green]")


def main():
    """Main entry point"""
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_demo()
    else:
        full_demo()


if __name__ == "__main__":
    main()
