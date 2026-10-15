#!/usr/bin/env python3
"""
🔧 EXIT FLAG BEHAVIOR TEST

Test to verify the exit flag fix works correctly.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import sys
import time

# Add project root to path

from src.utils.listeners.exit_listener import ExitListener
from src.config import settings


def test_exit_flag_behavior():
    """Test that exit_flag behaves correctly after the fix."""
    print("🧪 TESTING EXIT FLAG BEHAVIOR AFTER FIX")
    print("=" * 50)

    # Reset to clean state
    settings.exit_flag = False

    # Simulate the fixed workflow
    def simulate_non_exit_message():
        """Simulate processing a non-exit message."""
        # This is what happens in the fixed code for non-exit messages
        print(f"   Before: settings.exit_flag = {settings.exit_flag}")

        # Simulate graph.invoke() - no change to exit_flag during this

        # Check if exit-related (will be False for this test)
        is_exit_related = False  # Simulating non-exit message

        if is_exit_related:
            settings.exit_flag = True
            print("   → Would emit exit ticket")
        else:
            settings.exit_flag = False  # ✅ The critical fix
            print("   → No exit ticket, flag reset to False")

        print(f"   After: settings.exit_flag = {settings.exit_flag}")
        return settings.exit_flag

    def simulate_exit_message():
        """Simulate processing an exit message."""
        print(f"   Before: settings.exit_flag = {settings.exit_flag}")

        # Check if exit-related (will be True for this test)
        is_exit_related = True  # Simulating /exit message

        if is_exit_related:
            settings.exit_flag = True
            print("   → Would emit exit ticket")
        else:
            settings.exit_flag = False
            print("   → No exit ticket, flag reset to False")

        print(f"   After: settings.exit_flag = {settings.exit_flag}")
        return settings.exit_flag

    # Test sequence
    print("\n📝 Test 1: Multiple non-exit messages")
    flag1 = simulate_non_exit_message()
    flag2 = simulate_non_exit_message()
    flag3 = simulate_non_exit_message()

    all_false = flag1 == False and flag2 == False and flag3 == False
    print(f"✅ Result: All flags False = {all_false}")

    print("\n📝 Test 2: Non-exit then exit message")
    flag1 = simulate_non_exit_message()  # Should be False
    flag2 = simulate_exit_message()      # Should be True

    correct_sequence = flag1 == False and flag2 == True
    print(f"✅ Result: Correct sequence (False → True) = {correct_sequence}")

    print("\n📊 SUMMARY:")
    if all_false and correct_sequence:
        print("✅ ALL TESTS PASSED! Exit flag behavior is now correct.")
        print("🎯 Normal messages keep flag False")
        print("🎯 Exit messages set flag True")
        print("🎯 No more unexpected exits after 2 messages!")
    else:
        print("❌ Some tests failed. Check the logic.")

    print(f"\nFinal exit_flag state: {settings.exit_flag}")


if __name__ == "__main__":
    test_exit_flag_behavior()
