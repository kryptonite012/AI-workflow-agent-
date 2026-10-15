#!/usr/bin/env python3
"""
Test runner for all error handling tests
Runs all tests in the error_handling folder
"""

import os
import subprocess
import sys
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def run_test_file(test_file):
    """Run a single test file and return the result"""
    print(f"\n{'=' * 80}")
    print(f"🚀 RUNNING: {test_file}")
    print(f"{'=' * 80}")

    try:
        # Get the full path to the test file
        test_path = os.path.join(os.path.dirname(__file__), test_file)

        # Run the test file
        result = subprocess.run(
            [sys.executable, test_path], capture_output=False, text=True
        )

        if result.returncode == 0:
            print(f"✅ {test_file} completed successfully")
            return True
        else:
            print(f"❌ {test_file} failed with return code {result.returncode}")
            return False

    except Exception as e:
        print(f"❌ Failed to run {test_file}: {e}")
        return False


def check_prerequisites():
    """Check if prerequisites are met"""
    print("🔍 Checking Prerequisites...")

    # Check if config module can be imported
    try:
        import config

        print(f"✅ Config loaded - Socket: {config.SOCKET_HOST}:{config.SOCKET_PORT}")
        print(f"✅ Socket logging enabled: {config.ENABLE_SOCKET_LOGGING}")
    except ImportError as e:
        print(f"❌ Cannot import config: {e}")
        return False

    # Check if socket manager can be imported
    try:
        from utils.socket_manager import socket_manager

        print("✅ Socket manager imported successfully")
    except ImportError as e:
        print(f"❌ Cannot import socket manager: {e}")
        return False

    # Check if error_transfer can be imported
    try:
        from utils.error_transfer import SocketCon

        print("✅ SocketCon imported successfully")
    except ImportError as e:
        print(f"❌ Cannot import SocketCon: {e}")
        return False

    return True


def main():
    """Main test runner"""
    print("=" * 80)
    print("🧪 ERROR HANDLING TEST SUITE RUNNER")
    print("=" * 80)

    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix the issues above.")
        return

    print("\n📋 IMPORTANT INSTRUCTIONS:")
    print("   1. Start the log server FIRST: python utils/error_transfer.py")
    print("   2. Keep the log server running during all tests")
    print("   3. Check the log server terminal for received messages")
    print("   4. Some tests may show warnings if server is not running")

    input("\n⏸️  Press Enter when log server is ready (or Ctrl+C to cancel)...")

    # List of test files to run
    test_files = [
        "test_socket_connection.py",
        "test_socket_manager.py",
        "test_logging_system.py",
        "test_subprocess_logging.py",
    ]

    results = []
    start_time = time.time()

    # Run each test file
    for test_file in test_files:
        print(f"\n⏳ Starting {test_file}...")
        time.sleep(1)  # Small delay between tests

        result = run_test_file(test_file)
        results.append((test_file, result))

        if result:
            print(f"✅ {test_file} - PASSED")
        else:
            print(f"❌ {test_file} - FAILED")

        time.sleep(2)  # Pause between tests

    # Final summary
    end_time = time.time()
    duration = end_time - start_time

    print("\n" + "=" * 80)
    print("📊 FINAL TEST RESULTS SUMMARY")
    print("=" * 80)

    passed = 0
    for test_file, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_file}")
        if result:
            passed += 1

    print(f"\n📈 Overall Results:")
    print(f"   ✅ Passed: {passed}/{len(results)} test files")
    print(f"   ⏱️  Duration: {duration:.1f} seconds")

    if passed == len(results):
        print("\n🎉 ALL ERROR HANDLING TESTS PASSED!")
        print("   Your error handling system is working correctly.")
    else:
        print(f"\n⚠️  {len(results) - passed} test file(s) failed.")
        print("   Check the output above for details.")

    print("\n📋 Next Steps:")
    print("   1. Review any failed tests above")
    print("   2. Check the log server terminal for received messages")
    print("   3. Verify your socket configuration in config.py")
    print("   4. Make sure ENABLE_SOCKET_LOGGING=true")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Test suite interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite crashed: {e}")
