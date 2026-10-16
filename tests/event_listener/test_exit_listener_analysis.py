#!/usr/bin/env python3
"""
🔍 EXIT LISTENER DIAGNOSTIC TEST

This test analyzes why the ExitListener is not working and demonstrates the issues.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import sys
import time
import threading
from unittest.mock import patch, MagicMock

# Add project root to path

from src.utils.listeners.exit_listener import ExitListener
from src.utils.listeners.event_listener import EventListener
from src.config import settings


class ExitListenerDiagnostic:
    """Comprehensive diagnostic tool for ExitListener issues."""

    def __init__(self):
        self.test_results = []
        self.original_exit_flag = settings.exit_flag

    def log_test(self, test_name, passed, reason=""):
        """Log test results."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {test_name}")
        if reason:
            print(f"   📝 {reason}")
        self.test_results.append((test_name, passed, reason))

    def test_1_basic_initialization(self):
        """Test 1: Basic ExitListener initialization"""
        print("\n🧪 TEST 1: Basic Initialization")
        try:
            exit_listener = ExitListener()

            # Check if manager is created
            manager_exists = ExitListener.manager is not None
            self.log_test("Manager Creation", manager_exists,
                         f"Manager: {ExitListener.manager}")

            # Check if previous_exit_flag is set
            flag_initialized = hasattr(exit_listener, 'previous_exit_flag')
            self.log_test("Previous Flag Initialized", flag_initialized,
                         f"previous_exit_flag: {getattr(exit_listener, 'previous_exit_flag', 'NOT SET')}")

        except Exception as e:
            self.log_test("Basic Initialization", False, f"Exception: {e}")

    def test_2_filter_function_issues(self):
        """Test 2: Filter function problems"""
        print("\n🧪 TEST 2: Filter Function Analysis")

        exit_listener = ExitListener()

        # Problem 1: Filter function doesn't receive event_data parameter
        print("   🔍 Analyzing filter function signature...")

        # The filter function in register() is: lambda: self.check_condition()
        # But EventManager expects: filter_func(event_data) -> bool

        # Let's test what happens when EventManager calls the filter
        try:
            # Simulate how EventManager would call the filter
            filter_func = lambda: exit_listener.check_condition()

            # This should fail because EventManager passes event_data parameter
            mock_event_data = EventListener.EventData(
                event_type=EventListener.EventType.VARIABLE_CHANGED,
                source_class=ExitListener,
                meta_data={"test": "data"}
            )

            # Try calling filter with event_data (as EventManager does)
            try:
                result = filter_func(mock_event_data)  # This will fail!
                self.log_test("Filter Function Call", False, "Should have failed but didn't")
            except TypeError as e:
                self.log_test("Filter Function Call", False,
                             f"TypeError as expected: {e}")
                print(f"   💡 ISSUE: Filter lambda doesn't accept event_data parameter")

        except Exception as e:
            self.log_test("Filter Function Analysis", False, f"Unexpected error: {e}")

    def test_3_registration_issues(self):
        """Test 3: Registration problems"""
        print("\n🧪 TEST 3: Registration Issues")

        exit_listener = ExitListener()

        # Problem 1: Wrong callback in unregister
        print("   🔍 Checking registration vs unregistration...")

        # In register(): self.on_variable_change
        # In unregister(): self.on_event  <- WRONG!

        registered_callback = exit_listener.on_variable_change
        unregistered_callback = exit_listener.on_event

        callbacks_match = registered_callback == unregistered_callback
        self.log_test("Registration/Unregistration Callback Match", callbacks_match,
                     f"Registered: {registered_callback.__name__}, Unregistered: {unregistered_callback.__name__}")

        if not callbacks_match:
            print("   💡 ISSUE: register() uses 'on_variable_change' but unregister() uses 'on_event'")

    def test_4_event_emission_workflow(self):
        """Test 4: Event emission workflow"""
        print("\n🧪 TEST 4: Event Emission Workflow")

        exit_listener = ExitListener()

        # Problem: Nobody calls emit_on_variable_change when settings.exit_flag changes
        print("   🔍 Testing event emission workflow...")

        # Simulate settings.exit_flag changing
        original_flag = settings.exit_flag

        # Change the flag
        settings.exit_flag = True

        # Check if any event was emitted automatically
        print(f"   📊 Original flag: {original_flag}")
        print(f"   📊 Current flag: {settings.exit_flag}")
        print("   💡 ISSUE: settings.exit_flag changed but NO event was emitted automatically!")
        print("   💡 ISSUE: You need to manually call emit_on_variable_change() when settings.exit_flag changes")

        # Reset flag
        settings.exit_flag = original_flag

        self.log_test("Automatic Event Emission", False,
                     "settings.exit_flag changes don't automatically emit events")

    def test_5_complete_workflow_simulation(self):
        """Test 5: Complete workflow simulation"""
        print("\n🧪 TEST 5: Complete Workflow Simulation")

        exit_listener = ExitListener()

        # Let's fix the issues and test the complete workflow
        print("   🔧 Simulating fixed workflow...")

        # Create a proper filter function
        def proper_filter(event_data):
            return (event_data.meta_data and
                   event_data.meta_data.get("variable_name") == "exit_flag" and
                   event_data.meta_data.get("id") == id(exit_listener))

        # Register with proper filter
        exit_listener.manager.register_listener(
            EventListener.EventType.VARIABLE_CHANGED,
            exit_listener.on_variable_change,
            priority=10,
            filter_func=proper_filter
        )

        # Test event emission
        print("   📤 Emitting exit flag change event...")

        # Emit the event manually
        exit_listener.emit_on_variable_change(
            source_class=type(settings),
            variable_name="exit_flag",
            old_value=False,
            new_value=True
        )

        self.log_test("Manual Event Emission", True, "Event emitted successfully with proper workflow")

    def test_6_identify_missing_integration(self):
        """Test 6: Identify missing integration points"""
        print("\n🧪 TEST 6: Missing Integration Points")

        print("   🔍 Analyzing where ExitListener should be integrated...")

        missing_integrations = [
            "❌ ExitListener is never instantiated in main application",
            "❌ No automatic monitoring of settings.exit_flag changes",
            "❌ No integration with slash command handler",
            "❌ No integration with chat_initializer.py",
            "❌ No __setattr__ monitoring on settings module"
        ]

        for issue in missing_integrations:
            print(f"   {issue}")

        self.log_test("Integration Analysis", False, "Multiple integration points missing")

    def run_all_tests(self):
        """Run all diagnostic tests."""
        print("🔍 EXIT LISTENER DIAGNOSTIC ANALYSIS")
        print("=" * 50)

        # Reset to known state
        settings.exit_flag = self.original_exit_flag

        self.test_1_basic_initialization()
        self.test_2_filter_function_issues()
        self.test_3_registration_issues()
        self.test_4_event_emission_workflow()
        self.test_5_complete_workflow_simulation()
        self.test_6_identify_missing_integration()

        # Summary
        print("\n📊 DIAGNOSTIC SUMMARY")
        print("=" * 30)

        passed = sum(1 for _, passed, _ in self.test_results if passed)
        total = len(self.test_results)

        print(f"Tests Passed: {passed}/{total}")

        print("\n🛠️ ISSUES IDENTIFIED:")
        print("1. Filter function signature mismatch - lambda doesn't accept event_data parameter")
        print("2. Registration/unregistration callback mismatch - different methods used")
        print("3. No automatic event emission when settings.exit_flag changes")
        print("4. Missing integration points in main application")
        print("5. No monitoring mechanism for settings module changes")

        print("\n💡 SOLUTIONS NEEDED:")
        print("1. Fix filter function: lambda event_data: self.check_condition(event_data)")
        print("2. Fix unregister to use same callback as register")
        print("3. Add __setattr__ monitoring to settings module OR")
        print("4. Manually call emit_on_variable_change when exit_flag changes")
        print("5. Integrate ExitListener in chat_initializer.py")
        print("6. Connect slash command handler to emit events")


def main():
    """Run the diagnostic."""
    diagnostic = ExitListenerDiagnostic()
    diagnostic.run_all_tests()


if __name__ == "__main__":
    main()
