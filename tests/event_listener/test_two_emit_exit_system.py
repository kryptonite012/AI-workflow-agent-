#!/usr/bin/env python3
"""
🎫 TWO-EMIT EXIT SYSTEM TEST

This test verifies that the exit system only exits when BOTH tickets are received:
1. Workflow completion ticket
2. /exit command ticket
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


class TwoEmitExitSystemTest:
    """Test the two-emit exit system functionality."""

    def __init__(self):
        self.test_results = []
        self.original_exit_flag = settings.exit_flag
        self.exit_called = False

        # Mock sys.exit to prevent actual exit during testing
        self.original_exit = sys.exit
        sys.exit = self.mock_exit

    def mock_exit(self, code=0):
        """Mock sys.exit to capture exit calls without actually exiting."""
        self.exit_called = True
        print(f"🚪 MOCK EXIT CALLED with code {code}")

    def log_test(self, test_name, passed, reason=""):
        """Log test results."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {test_name}")
        if reason:
            print(f"   📝 {reason}")
        self.test_results.append((test_name, passed, reason))

    def reset_test_environment(self):
        """Reset the test environment for each test."""
        settings.exit_flag = False
        self.exit_called = False
        # Create fresh ExitListener instance
        return ExitListener()

    def test_1_single_ticket_no_exit(self):
        """Test 1: Single ticket should NOT trigger exit"""
        print("\n🧪 TEST 1: Single Ticket (No Exit)")

        exit_listener = self.reset_test_environment()
        exit_listener.register()

        # Emit only one ticket
        exit_listener.emit_exit_ticket(
            source_class=type(self),
            source_name="test_single_ticket"
        )

        # Wait briefly for event processing
        time.sleep(0.1)

        # Should NOT have exited
        should_not_exit = not self.exit_called
        ticket_count_correct = exit_listener.exit_tickets_received == 1

        self.log_test("Single Ticket No Exit", should_not_exit and ticket_count_correct,
                     f"Exit called: {self.exit_called}, Tickets: {exit_listener.exit_tickets_received}/2")

        exit_listener.unregister()

    def test_2_two_tickets_should_exit(self):
        """Test 2: Two tickets should trigger exit"""
        print("\n🧪 TEST 2: Two Tickets (Should Exit)")

        exit_listener = self.reset_test_environment()
        exit_listener.register()

        # Emit first ticket
        exit_listener.emit_exit_ticket(
            source_class=type(self),
            source_name="workflow_completion"
        )

        time.sleep(0.1)

        # Should not have exited yet
        first_ticket_no_exit = not self.exit_called

        # Emit second ticket
        exit_listener.emit_exit_ticket(
            source_class=type(self),
            source_name="/exit_command"
        )

        time.sleep(0.1)

        # Should have exited now
        second_ticket_exit = self.exit_called
        ticket_count_correct = exit_listener.exit_tickets_received == 2

        self.log_test("Two Tickets Exit", first_ticket_no_exit and second_ticket_exit and ticket_count_correct,
                     f"First: no exit({first_ticket_no_exit}), Second: exit({second_ticket_exit}), Tickets: {exit_listener.exit_tickets_received}/2")

        exit_listener.unregister()

    def test_3_ticket_source_tracking(self):
        """Test 3: Verify ticket sources are tracked correctly"""
        print("\n🧪 TEST 3: Ticket Source Tracking")

        exit_listener = self.reset_test_environment()
        exit_listener.register()

        # Emit tickets with specific sources
        exit_listener.emit_exit_ticket(
            source_class=type(self),
            source_name="workflow_completion"
        )

        exit_listener.emit_exit_ticket(
            source_class=type(self),
            source_name="/exit_command"
        )

        time.sleep(0.1)

        # Check source tracking
        expected_sources = ["workflow_completion", "/exit_command"]
        sources_correct = exit_listener.ticket_sources == expected_sources

        self.log_test("Ticket Source Tracking", sources_correct,
                     f"Expected: {expected_sources}, Got: {exit_listener.ticket_sources}")

        exit_listener.unregister()

    def test_4_exit_flag_behavior(self):
        """Test 4: Verify exit_flag is set correctly"""
        print("\n🧪 TEST 4: Exit Flag Behavior")

        exit_listener = self.reset_test_environment()
        exit_listener.register()

        # Initial state
        initial_flag = settings.exit_flag  # Should be False

        # Emit first ticket
        exit_listener.emit_exit_ticket(
            source_class=type(self),
            source_name="workflow_completion"
        )

        # Flag should now be True
        after_first_ticket = settings.exit_flag

        # Emit second ticket
        exit_listener.emit_exit_ticket(
            source_class=type(self),
            source_name="/exit_command"
        )

        # Flag should still be True
        after_second_ticket = settings.exit_flag

        time.sleep(0.1)

        flag_behavior_correct = (
            initial_flag == False and
            after_first_ticket == True and
            after_second_ticket == True
        )

        self.log_test("Exit Flag Behavior", flag_behavior_correct,
                     f"Initial: {initial_flag}, After 1st: {after_first_ticket}, After 2nd: {after_second_ticket}")

        exit_listener.unregister()

    def test_5_realistic_workflow_simulation(self):
        """Test 5: Simulate realistic workflow"""
        print("\n🧪 TEST 5: Realistic Workflow Simulation")

        exit_listener = self.reset_test_environment()
        exit_listener.register()

        print("   📝 User types '/exit' command...")
        # Simulate /exit command (second ticket)
        exit_listener.emit_exit_ticket(
            source_class=type(self),
            source_name="/exit_command"
        )

        time.sleep(0.1)
        should_not_exit_yet = not self.exit_called

        print("   📝 Workflow completes...")
        # Simulate workflow completion (first ticket)
        exit_listener.emit_exit_ticket(
            source_class=type(self),
            source_name="workflow_completion"
        )

        time.sleep(0.1)
        should_exit_now = self.exit_called

        workflow_correct = should_not_exit_yet and should_exit_now

        self.log_test("Realistic Workflow", workflow_correct,
                     f"After /exit: no exit({should_not_exit_yet}), After workflow: exit({should_exit_now})")

        exit_listener.unregister()

    def test_6_edge_case_multiple_tickets(self):
        """Test 6: Edge case - more than 2 tickets"""
        print("\n🧪 TEST 6: Edge Case - Multiple Tickets")

        exit_listener = self.reset_test_environment()
        exit_listener.register()

        # Emit 3 tickets
        for i in range(3):
            exit_listener.emit_exit_ticket(
                source_class=type(self),
                source_name=f"ticket_{i+1}"
            )
            time.sleep(0.05)

        # Should have exited after 2nd ticket
        ticket_count = exit_listener.exit_tickets_received
        exit_behavior = self.exit_called

        self.log_test("Multiple Tickets Edge Case", exit_behavior and ticket_count >= 2,
                     f"Tickets received: {ticket_count}, Exit called: {exit_behavior}")

        exit_listener.unregister()

    def cleanup(self):
        """Cleanup after tests."""
        # Restore original sys.exit
        sys.exit = self.original_exit
        settings.exit_flag = self.original_exit_flag

    def run_all_tests(self):
        """Run all tests."""
        print("🎫 TWO-EMIT EXIT SYSTEM TEST")
        print("=" * 50)

        self.test_1_single_ticket_no_exit()
        self.test_2_two_tickets_should_exit()
        self.test_3_ticket_source_tracking()
        self.test_4_exit_flag_behavior()
        self.test_5_realistic_workflow_simulation()
        self.test_6_edge_case_multiple_tickets()

        # Summary
        print("\n📊 TEST SUMMARY")
        print("=" * 30)

        passed = sum(1 for _, passed, _ in self.test_results if passed)
        total = len(self.test_results)

        print(f"Tests Passed: {passed}/{total}")

        if passed == total:
            print("\n✅ ALL TESTS PASSED! Two-emit exit system is working correctly.")
            print("\n🎯 SYSTEM BEHAVIOR:")
            print("• Single ticket = No exit (waits for second ticket)")
            print("• Two tickets = Immediate exit with graceful message")
            print("• Ticket sources are tracked correctly")
            print("• Exit flag is managed properly")
        else:
            print(f"\n❌ {total - passed} test(s) failed. Check the implementation.")

        self.cleanup()


def main():
    """Run the test suite."""
    test_suite = TwoEmitExitSystemTest()
    test_suite.run_all_tests()


if __name__ == "__main__":
    main()
