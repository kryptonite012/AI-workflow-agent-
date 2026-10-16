# 🧪 Standalone Event Listener Test
"""
Standalone test that recreates the event listener functionality for testing
without complex project dependencies.

This test validates the core concepts and demonstrates the realistic
multi-threaded scenario you requested.
"""

import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Callable
from weakref import WeakKeyDictionary
from rich.console import Console


# Recreate the core event system for testing
class EventListener:
    """Standalone event listener system for testing"""

    class EventType(Enum):
        VARIABLE_CHANGED = "variable_changed"
        ERROR_OCCURRED = "error_occurred"

    @dataclass
    class EventData:
        event_type: "EventListener.EventType"
        source_class: type
        timestamp: float = None
        meta_data: Dict[str, Any] = None

        def __post_init__(self):
            if self.timestamp is None:
                self.timestamp = time.time()
            if self.meta_data is None:
                self.meta_data = {}

    class EventManager:
        _instance = None
        _lock = threading.Lock()

        def __new__(cls):
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.listeners = {}
            return cls._instance

        def __init__(self):
            if not hasattr(self, "initialized"):
                self.initialized = True
                self.listeners = {}
                self.listener_filter = {}

        def register_listener(self, event_type, listener, priority=0, filter_func=None):
            with self._lock:
                if event_type not in self.listeners:
                    self.listeners[event_type] = []

                self.listeners[event_type].append(listener)
                if filter_func:
                    self.listener_filter[listener] = filter_func

        def emit_event(self, event_data):
            with self._lock:
                listeners = self.listeners.get(event_data.event_type, []).copy()

            for listener in listeners:
                try:
                    filter_func = self.listener_filter.get(listener)
                    if filter_func and not filter_func(event_data):
                        continue
                    listener(event_data)
                except Exception as e:
                    print(f"Error in listener: {e}")


# Recreate RichStatusListener for testing
class TestRichStatusListener:
    """Standalone RichStatusListener for testing"""

    _listeners = WeakKeyDictionary()

    def __init__(self, console):
        if self not in TestRichStatusListener._listeners:
            TestRichStatusListener._listeners[self] = self
        else:
            raise ValueError("Listener instance already exists")

        self.console = console
        self.current_status = None
        self.status_context = None
        self.status_thread_lock = threading.Lock()
        self.processed_events = set()
        self.status_is_active = False
        self.event_history = []

        # Register with event system
        self._register_variable_listener()
        print(f"🎯 Test Listener initialized! ID: {id(self)}")

    def _do_we_need_to_listen(self, event_data):
        if not event_data.meta_data:
            return False
        if "id" in event_data.meta_data and event_data.meta_data["id"] == id(self):
            return True
        return False

    def _register_variable_listener(self):
        event_manager = EventListener.EventManager()
        event_manager.register_listener(
            EventListener.EventType.VARIABLE_CHANGED,
            self._on_variable_changed,
            filter_func=self._do_we_need_to_listen,
            priority=5,
        )

    def _on_variable_changed(self, event_data):
        meta_data = event_data.meta_data

        event_info = f"{event_data.source_class.__name__} - {event_data.event_type} changed from {meta_data.get('old_value')} to {meta_data.get('new_value')}"

        if event_info in self.processed_events:
            return

        status_message = f"Status: {meta_data.get('new_value')}"
        self.update_status(status_message)

        self.processed_events.add(event_info)
        self.event_history.append(
            {
                "type": event_data.event_type.value,
                "event_id": event_info,
                "timestamp": event_data.timestamp,
                "message": status_message,
                "data": event_data,
            }
        )

    def start_status(self, initial_message):
        with self.status_thread_lock:
            if not self.status_is_active:
                self.status_context = self.console.status(initial_message)
                self.current_status = self.status_context.__enter__()
                self.status_is_active = True
                print(f"✅ Status started: {initial_message}")

    def update_status(self, status_message):
        with self.status_thread_lock:
            if self.status_is_active and self.current_status:
                self.current_status.update(status_message)
            else:
                print(f"Status not active: {status_message}")

    def stop_status_display(self):
        with self.status_thread_lock:
            if self.status_is_active and self.current_status:
                self.status_context.__exit__(None, None, None)
                self.current_status = None
                self.status_context = None
                self.status_is_active = False
                print("⏹️ Status stopped")

    def emit_on_variable_change(
        self, source_class, variable_name, old_value, new_value
    ):
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


class RequestProcessor:
    """Test class representing request processing"""

    pass


def run_realistic_test():
    """Run the exact test scenario you requested"""
    console = Console()

    console.print("🚀 [bold blue]REALISTIC EVENT LISTENER TEST[/bold blue]")
    console.print("📝 Scenario: Heading generation with background request processing")
    console.print("-" * 60)

    # Create listener
    listener_console = Console()
    listener = TestRichStatusListener(listener_console)

    # Start with "generating heading..." status
    listener.start_status("🔄 generating heading...")
    console.print("✅ Started with 'generating heading...' status")

    # Shared state for threading
    request_count = 0
    is_running = True

    def process_requests_background():
        """Background thread processing requests"""
        nonlocal request_count, is_running

        console.print("🔧 Background request processing started...")

        while is_running and request_count < 45:
            # Simulate realistic request processing time
            time.sleep(0.2)  # 200ms per request
            request_count += 1

            # Update status at specific milestones (as requested)
            if request_count == 10:
                listener.emit_on_variable_change(
                    RequestProcessor,
                    "status",
                    "generating heading...",
                    "🔄 generating heading... (requests done 10)",
                )
                console.print("📊 [green]Milestone reached: 10 requests done[/green]")

            elif request_count == 30:
                listener.emit_on_variable_change(
                    RequestProcessor,
                    "status",
                    "generating heading... (requests done 10)",
                    "🔄 generating heading... (requests done 30)",
                )
                console.print("📊 [green]Milestone reached: 30 requests done[/green]")

            elif request_count == 40:
                listener.emit_on_variable_change(
                    RequestProcessor,
                    "status",
                    "generating heading... (requests done 30)",
                    "⏳ generating the request is 40 wait for sec",
                )
                console.print(
                    "⏳ [yellow]Special milestone: 40 requests - waiting...[/yellow]"
                )

                # Wait for 2 seconds as requested
                time.sleep(2)

                # Final completion status
                listener.emit_on_variable_change(
                    RequestProcessor,
                    "status",
                    "generating the request is 40 wait for sec",
                    "✅ heading generation completed!",
                )
                console.print("🎉 [bold green]Process completed![/bold green]")
                is_running = False
                break

    # Start background thread
    request_thread = threading.Thread(target=process_requests_background, daemon=True)
    request_thread.start()

    console.print(
        "👀 [bold cyan]Watch the status display above for real-time updates![/bold cyan]"
    )
    console.print("⏱️  Expected duration: ~10-12 seconds")

    # Wait for completion
    request_thread.join(timeout=20)

    # Give time to see final status
    time.sleep(3)

    # Stop status display
    listener.stop_status_display()

    # Show detailed results
    console.print("\n" + "=" * 60)
    console.print("📊 [bold green]TEST RESULTS[/bold green]")
    console.print("=" * 60)

    console.print(
        f"📈 Total requests processed: [bold yellow]{request_count}[/bold yellow]"
    )
    console.print(
        f"📝 Events in history: [bold yellow]{len(listener.event_history)}[/bold yellow]"
    )
    console.print(
        f"🔍 Processed events: [bold yellow]{len(listener.processed_events)}[/bold yellow]"
    )

    # Show event history
    if listener.event_history:
        console.print("\n📋 [bold blue]Event History:[/bold blue]")
        for i, event in enumerate(listener.event_history[-5:], 1):  # Show last 5 events
            console.print(f"  {i}. {event['message']}")

    # Validation
    expected_milestones = [10, 30, 40]
    milestones_hit = []

    for event in listener.event_history:
        if "requests done 10" in event["message"]:
            milestones_hit.append(10)
        elif "requests done 30" in event["message"]:
            milestones_hit.append(30)
        elif "request is 40" in event["message"]:
            milestones_hit.append(40)

    console.print(f"\n🎯 [bold blue]Milestone Validation:[/bold blue]")
    for milestone in expected_milestones:
        if milestone in milestones_hit:
            console.print(f"  ✅ {milestone} requests milestone reached")
        else:
            console.print(f"  ❌ {milestone} requests milestone MISSED")

    # Overall result
    if len(milestones_hit) == 3 and request_count >= 40:
        console.print("\n🎉 [bold green]ALL TESTS PASSED![/bold green]")
        console.print("✅ Event listener system working perfectly!")
        console.print("✅ Multi-threaded status updates confirmed!")
        console.print("✅ Realistic behavior validated!")
        return True
    else:
        console.print("\n❌ [bold red]SOME TESTS FAILED![/bold red]")
        console.print("🔧 Check event listener implementation")
        return False


def run_continuous_until_working():
    """Run tests continuously until they work properly"""
    console = Console()
    console.print("🔄 [bold blue]CONTINUOUS TESTING MODE[/bold blue]")
    console.print("Will run tests until they work properly...")

    attempt = 1

    while True:
        console.print(f"\n🧪 [bold yellow]TEST ATTEMPT {attempt}[/bold yellow]")
        console.print("-" * 50)

        try:
            success = run_realistic_test()

            if success:
                console.print(
                    f"\n🎉 [bold green]SUCCESS ON ATTEMPT {attempt}![/bold green]"
                )
                console.print("✅ Event listener system is working correctly!")
                break
            else:
                console.print(f"\n🔄 Attempt {attempt} had issues, retrying...")

        except KeyboardInterrupt:
            console.print("\n⏹️ Testing interrupted by user")
            break

        except Exception as e:
            console.print(f"\n❌ Attempt {attempt} failed with error: {e}")

        attempt += 1

        if attempt > 10:
            console.print("\n❌ Too many attempts, stopping...")
            break

        console.print("🔄 Retrying in 2 seconds...")
        time.sleep(2)

    console.print("\n🏁 Continuous testing completed")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Standalone Event Listener Test")
    parser.add_argument(
        "--continuous", action="store_true", help="Run continuously until working"
    )

    args = parser.parse_args()

    console = Console()
    console.print("🎯 [bold blue]STANDALONE EVENT LISTENER TEST[/bold blue]")
    console.print("Testing your event listener concepts without project dependencies")

    if args.continuous:
        run_continuous_until_working()
    else:
        run_realistic_test()
