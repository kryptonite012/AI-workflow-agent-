#!/usr/bin/env python3
"""
Main test runner for the entire test suite
Runs all tests in organized categories
"""

import os
import subprocess
import sys
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def run_test_category(category_name, test_files):
    """Run all tests in a category"""
    print(f"\n{'=' * 80}")
    print(f"🚀 RUNNING CATEGORY: {category_name}")
    print(f"{'=' * 80}")

    category_results = []

    for test_file in test_files:
        print(f"\n⏳ Running {test_file}...")

        try:
            # Get the full path to the test file
            test_path = os.path.join(os.path.dirname(__file__), test_file)

            # Run the test file
            result = subprocess.run(
                [sys.executable, test_path], capture_output=False, text=True
            )

            if result.returncode == 0:
                print(f"✅ {test_file} - PASSED")
                category_results.append((test_file, True))
            else:
                print(f"❌ {test_file} - FAILED (return code {result.returncode})")
                category_results.append((test_file, False))

        except Exception as e:
            print(f"❌ {test_file} - CRASHED: {e}")
            category_results.append((test_file, False))

        time.sleep(1)  # Small delay between tests

    return category_results


def show_instructions():
    """Show instructions for running tests"""
    print("📋 TEST SUITE INSTRUCTIONS")
    print("=" * 50)
    print("1. UNIT TESTS - Can run anytime, no prerequisites")
    print("2. ERROR HANDLING TESTS - Require log server running:")
    print("   → Start log server: python utils/error_transfer.py")
    print("   → Keep it running during tests")
    print("3. Check config.py for correct socket settings")
    print("4. Ensure ENABLE_SOCKET_LOGGING=true in config")
    print()


def main():
    """Main test runner"""
    print("=" * 80)
    print("🧪 LANGGRAPH CHATBOT - COMPLETE TEST SUITE")
    print("=" * 80)

    show_instructions()

    # Define test categories and their files
    test_categories = {
        "Unit Tests": ["unit/test_class_examples.py"],
        "Error Handling Tests": [
            "error_handling/test_socket_connection.py",
            "error_handling/test_socket_manager.py",
            "error_handling/test_logging_system.py",
            "error_handling/test_subprocess_logging.py",
        ],
    }

    print("🎯 Available test categories:")
    for i, category in enumerate(test_categories.keys(), 1):
        print(f"   {i}. {category}")

    print("\nOptions:")
    print("   A. Run ALL tests")
    print("   1. Run Unit Tests only")
    print("   2. Run Error Handling Tests only")
    print("   Q. Quit")

    choice = input("\n🤔 What would you like to run? (A/1/2/Q): ").strip().upper()

    if choice == "Q":
        print("👋 Goodbye!")
        return

    # Determine which categories to run
    categories_to_run = {}

    if choice == "A":
        categories_to_run = test_categories
    elif choice == "1":
        categories_to_run = {"Unit Tests": test_categories["Unit Tests"]}
    elif choice == "2":
        categories_to_run = {
            "Error Handling Tests": test_categories["Error Handling Tests"]
        }
        print("\n⚠️  IMPORTANT: Make sure log server is running!")
        print("   Command: python utils/error_transfer.py")
        input("   Press Enter when ready (or Ctrl+C to cancel)...")
    else:
        print("❌ Invalid choice. Please run again.")
        return

    # Run selected test categories
    all_results = {}
    start_time = time.time()

    for category_name, test_files in categories_to_run.items():
        category_results = run_test_category(category_name, test_files)
        all_results[category_name] = category_results

        # Show category summary
        passed = sum(1 for _, result in category_results if result)
        total = len(category_results)
        print(f"\n📊 {category_name} Summary: {passed}/{total} tests passed")

        time.sleep(2)  # Pause between categories

    # Final comprehensive summary
    end_time = time.time()
    duration = end_time - start_time

    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
    print("=" * 80)

    total_passed = 0
    total_tests = 0

    for category_name, category_results in all_results.items():
        print(f"\n🏷️  {category_name}:")

        category_passed = 0
        for test_file, result in category_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status} - {test_file}")
            if result:
                category_passed += 1

        print(f"   📈 Category Total: {category_passed}/{len(category_results)} passed")

        total_passed += category_passed
        total_tests += len(category_results)

    print(f"\n🎯 OVERALL RESULTS:")
    print(f"   ✅ Total Passed: {total_passed}/{total_tests} tests")
    print(f"   ⏱️  Total Duration: {duration:.1f} seconds")
    print(f"   📊 Success Rate: {(total_passed / total_tests) * 100:.1f}%")

    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("   Your system is working correctly!")
    else:
        failed = total_tests - total_passed
        print(f"\n⚠️  {failed} test(s) failed.")
        print("   Review the output above for details.")

    print("\n📋 Next Steps:")
    if total_passed == total_tests:
        print("   ✅ System is ready for use!")
        print("   ✅ All components are working correctly!")
    else:
        print("   🔧 Fix any failed tests")
        print("   🔍 Check error messages above")
        print("   📖 Review documentation for troubleshooting")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Test suite interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite crashed: {e}")
        import traceback

        traceback.print_exc()
