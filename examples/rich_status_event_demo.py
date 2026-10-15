# 🎯 Rich Status Event System Demo
"""
Complete demonstration of the Rich Status Event System

This example shows how to use the event system to automatically
update Rich.status display when variables change.

Run this file to see the Rich.status system in action!

Usage:
    python examples/rich_status_event_demo.py
"""

import time
import sys
import os

# Import from examples folder (following the user's pattern)
from rich_status_listener import rich_status_listener
from event_decorators import (
    make_class_event_aware,
    EventAwareBase,
    event_aware_property,
)
from event_helpers import emit_status_event, emit_error_event, progress_update


# Example 1: Using class decorator
@make_class_event_aware
class FileProcessor:
    """
    Example class that automatically emits events for ALL attribute changes
    """

    def __init__(self):
        self.status = "idle"
        self.files_processed = 0
        self.current_file = None
        self.error_count = 0

    def process_files(self, file_list):
        """Process a list of files with automatic Rich.status updates"""
        # Manual status event
        emit_status_event(self.__class__, "🚀 Starting file processing...")

        self.status = "processing"  # 🎯 Automatically updates Rich.status!

        for i, filename in enumerate(file_list):
            # Simulate file processing
            self.current_file = filename  # 🎯 Automatically updates Rich.status!
            time.sleep(0.5)  # Simulate processing time

            # Update progress
            self.files_processed = i + 1  # 🎯 Automatically updates Rich.status!

            # Simulate occasional errors
            if "error" in filename.lower():
                self.error_count += 1  # 🎯 Automatically updates Rich.status!
                emit_error_event(self.__class__, f"Failed to process {filename}")

            # Progress update
            progress_update(self.__class__, i + 1, len(file_list), "File Processing")

        self.status = "completed"  # 🎯 Automatically updates Rich.status!
        emit_status_event(self.__class__, "✅ File processing completed!")


# Example 2: Using base class
class DatabaseManager(EventAwareBase):
    """
    Example class using EventAwareBase for automatic event emission
    """

    def __init__(self):
        super().__init__()
        self.connection_count = 0
        self.query_time = 0.0
        self.last_query = None

    def connect(self):
        """Simulate database connection"""
        self.emit_status("🔌 Connecting to database...")
        time.sleep(0.3)  # Simulate connection time

        self.connection_count += 1  # 🎯 Automatically updates Rich.status!
        self.emit_status(f"✅ Connected! Total connections: {self.connection_count}")

    def execute_query(self, query):
        """Simulate query execution"""
        self.emit_status(f"🔍 Executing query: {query[:30]}...")

        # Simulate query execution
        start_time = time.time()
        time.sleep(0.2)  # Simulate query time
        end_time = time.time()

        self.query_time = end_time - start_time  # 🎯 Automatically updates Rich.status!
        self.last_query = query  # 🎯 Automatically updates Rich.status!

        self.emit_status(f"✅ Query completed in {self.query_time:.3f}s")


# Example 3: Using property descriptors
class DataAnalyzer:
    """
    Example class using property descriptors for specific attributes
    """

    # Only these properties will emit events
    progress = event_aware_property()
    status = event_aware_property()
    results_count = event_aware_property()

    def __init__(self):
        self.progress = 0
        self.status = "idle"
        self.results_count = 0
        self.internal_data = {}  # This won't emit events

    def analyze_data(self, data_size=100):
        """Analyze data with progress updates"""
        emit_status_event(self.__class__, "🔬 Starting data analysis...")

        self.status = "analyzing"  # 🎯 Automatically updates Rich.status!

        for i in range(0, data_size + 1, 10):
            time.sleep(0.2)  # Simulate analysis work

            self.progress = i  # 🎯 Automatically updates Rich.status!

            # Simulate finding results
            if i > 0 and i % 20 == 0:
                self.results_count += 5  # 🎯 Automatically updates Rich.status!

        self.status = "completed"  # 🎯 Automatically updates Rich.status!
        emit_status_event(
            self.__class__, f"✅ Analysis completed! Found {self.results_count} results"
        )


def demo_rich_status_system():
    """
    Complete demonstration of the Rich Status Event System
    """
    print("🎯 Rich Status Event System Demo")
    print("=" * 50)

    # Start Rich.status display
    rich_status_listener.start_status_display("🚀 Demo starting...")

    try:
        # Demo 1: File Processing
        print("\n📁 Demo 1: File Processing (Class Decorator)")
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
        print("\n🗄️ Demo 2: Database Operations (Base Class)")
        db_manager = DatabaseManager()

        db_manager.connect()
        db_manager.execute_query("SELECT * FROM users WHERE active = 1")
        db_manager.execute_query("UPDATE users SET last_login = NOW()")
        db_manager.connect()  # Another connection

        time.sleep(2)  # Pause between demos

        # Demo 3: Data Analysis
        print("\n🔬 Demo 3: Data Analysis (Property Descriptors)")
        analyzer = DataAnalyzer()

        analyzer.analyze_data(50)  # Smaller dataset for demo

        time.sleep(2)  # Final pause

        # Show statistics
        print("\n📊 Event System Statistics:")
        rich_status_listener.show_event_statistics()

        print("\n📋 Recent Events:")
        rich_status_listener.show_recent_events(15)

        # Final status
        emit_status_event("DemoSystem", "🎉 Demo completed successfully!")

        time.sleep(3)  # Let user see final status

    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
        emit_status_event("DemoSystem", "⏹️ Demo stopped by user")

    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        emit_error_event("DemoSystem", f"Demo failed: {str(e)}")

    finally:
        # Stop Rich.status display
        time.sleep(1)
        rich_status_listener.stop_status_display()

        print("\n🎯 Demo completed!")
        print("=" * 50)

        # Show final statistics
        info = rich_status_listener.get_status_info()
        print(f"📊 Final Stats: {info}")


def quick_demo():
    """
    Quick demo for testing
    """
    print("🚀 Quick Rich Status Demo")

    # Start status
    rich_status_listener.start_status_display("🧪 Quick test...")

    # Create a simple event-aware class
    @make_class_event_aware
    class TestClass:
        def __init__(self):
            self.counter = 0
            self.status = "ready"

    # Test it
    test_obj = TestClass()

    for i in range(5):
        test_obj.counter = i  # Should update Rich.status
        test_obj.status = f"step_{i}"  # Should update Rich.status
        time.sleep(0.5)

    emit_status_event(TestClass, "✅ Quick test completed!")
    time.sleep(2)

    # Stop status
    rich_status_listener.stop_status_display()
    print("✅ Quick demo completed!")


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_demo()
    else:
        demo_rich_status_system()
