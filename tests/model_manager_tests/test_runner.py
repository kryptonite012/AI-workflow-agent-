"""
Test runner for all ModelManager tests
"""

import os
import sys
from pathlib import Path

# Ensure project root is on sys.path for src imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import all test modules
from tests.model_manager_tests.test_singleton_behavior import TestModelManagerSingleton
from tests.model_manager_tests.test_model_loading import TestModelManagerLoading
from tests.model_manager_tests.test_integration import TestModelManagerIntegration
from tests.model_manager_tests.test_error_handling import TestModelManagerErrorHandling
from tests.model_manager_tests.test_thread_safety import TestModelManagerThreadSafety


def create_test_suite():
    """Create a comprehensive test suite for ModelManager"""
    suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        TestModelManagerSingleton,
        TestModelManagerLoading,
        TestModelManagerIntegration,
        TestModelManagerErrorHandling,
        TestModelManagerThreadSafety,
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    return suite


def run_specific_test_class(test_class_name):
    """Run a specific test class"""
    test_classes = {
        "singleton": TestModelManagerSingleton,
        "loading": TestModelManagerLoading,
        "integration": TestModelManagerIntegration,
        "error": TestModelManagerErrorHandling,
        "thread": TestModelManagerThreadSafety,
    }

    if test_class_name.lower() in test_classes:
        suite = unittest.TestLoader().loadTestsFromTestCase(
            test_classes[test_class_name.lower()]
        )
        runner = unittest.TextTestRunner(verbosity=2)
        return runner.run(suite)
    else:
        print(f"Available test classes: {list(test_classes.keys())}")
        return None


def main():
    """Main test runner function"""
    if len(sys.argv) > 1:
        # Run specific test class
        test_class = sys.argv[1]
        result = run_specific_test_class(test_class)
    else:
        # Run all tests
        suite = create_test_suite()
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

    # Return appropriate exit code
    if result and not result.wasSuccessful():
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
