"""
Automated API error simulation test for OpenAI integration.
Tests 502 error handling, retry logic, and circuit breaker functionality.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import sys
import os
import time
import json
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path

from src.utils.open_ai_integration import OpenAIIntegration
import openai


class APIErrorTestSuite:
    """Test suite for API error handling and recovery."""

    def __init__(self):
        self.test_results = {
            "502_handling": False,
            "retry_logic": False,
            "circuit_breaker": False,
            "fallback_responses": False,
            "recovery": False,
        }
        self.errors = []

    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results."""
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_symbol} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        if status == "FAIL":
            self.errors.append(f"{test_name}: {details}")

    def test_502_error_handling(self) -> bool:
        """Test 502 Bad Gateway error handling."""
        print("\n🔧 Testing 502 Error Handling...")

        try:
            integration = OpenAIIntegration()

            # Mock 502 error - create proper mock response and body
            mock_response = Mock()
            mock_response.status_code = 502
            mock_response.headers = {}
            mock_body = "Bad Gateway"
            mock_error = openai.APIStatusError(
                "Error code: 502", response=mock_response, body=mock_body
            )

            with patch.object(
                integration.client.chat.completions, "create", side_effect=mock_error
            ):
                result = integration.generate_text("Test message")

                # Should return fallback response, not crash
                if result and len(result) > 10:
                    self.log_test(
                        "502 Error Handling", "PASS", "Returned fallback response"
                    )
                    return True
                else:
                    self.log_test("502 Error Handling", "FAIL", "No fallback response")
                    return False

        except Exception as e:
            self.log_test("502 Error Handling", "FAIL", str(e))
            return False

    def test_retry_logic(self) -> bool:
        """Test retry logic with exponential backoff."""
        print("\n🔧 Testing Retry Logic...")

        try:
            integration = OpenAIIntegration()

            # Track retry attempts
            attempt_count = 0

            def mock_502_then_success(*args, **kwargs):
                nonlocal attempt_count
                attempt_count += 1
                if attempt_count <= 2:  # Fail first 2 attempts
                    mock_response = Mock()
                    mock_response.status_code = 502
                    mock_response.headers = {}
                    raise openai.APIStatusError(
                        "Error code: 502", response=mock_response, body="Bad Gateway"
                    )
                else:
                    # Return mock successful response
                    mock_response = Mock()
                    mock_response.choices = [Mock()]
                    mock_response.choices[0].message = Mock()
                    mock_response.choices[0].message.content = "Success after retry"
                    return mock_response

            with patch.object(
                integration.client.chat.completions,
                "create",
                side_effect=mock_502_then_success,
            ):
                start_time = time.time()
                result = integration.generate_text("Test message")
                elapsed_time = time.time() - start_time

                # Should succeed after retries and take some time due to backoff
                if result == "Success after retry" and elapsed_time > 1:
                    self.log_test(
                        "Retry Logic",
                        "PASS",
                        f"Succeeded after {attempt_count} attempts in {elapsed_time:.1f}s",
                    )
                    return True
                else:
                    self.log_test("Retry Logic", "FAIL", f"Unexpected result: {result}")
                    return False

        except Exception as e:
            self.log_test("Retry Logic", "FAIL", str(e))
            return False

    def test_circuit_breaker(self) -> bool:
        """Test circuit breaker functionality."""
        print("\n🔧 Testing Circuit Breaker...")

        try:
            # Reset circuit breaker state
            OpenAIIntegration._failure_count = 0
            OpenAIIntegration._circuit_open = False
            OpenAIIntegration._circuit_open_until = None

            integration = OpenAIIntegration()

            # Simulate multiple failures to trigger circuit breaker
            mock_response = Mock()
            mock_response.status_code = 502
            mock_response.headers = {}
            mock_error = openai.APIStatusError(
                "Error code: 502", response=mock_response, body="Bad Gateway"
            )

            with patch.object(
                integration.client.chat.completions, "create", side_effect=mock_error
            ):
                # Make enough failed calls to open circuit
                for i in range(6):  # More than _max_failures (5)
                    try:
                        integration.generate_text(f"Test message {i}")
                    except:
                        pass

                # Check if circuit breaker is open
                if OpenAIIntegration._circuit_open:
                    self.log_test(
                        "Circuit Breaker",
                        "PASS",
                        f"Circuit opened after {OpenAIIntegration._failure_count} failures",
                    )
                    return True
                else:
                    self.log_test(
                        "Circuit Breaker", "FAIL", "Circuit breaker did not open"
                    )
                    return False

        except Exception as e:
            self.log_test("Circuit Breaker", "FAIL", str(e))
            return False

    def test_fallback_responses(self) -> bool:
        """Test different types of fallback responses."""
        print("\n🔧 Testing Fallback Responses...")

        try:
            integration = OpenAIIntegration()

            # Test classification fallback
            classification_fallback = integration._get_fallback_response(
                "classification"
            )
            if "message_type" not in classification_fallback:
                self.log_test(
                    "Fallback Responses", "FAIL", "Classification fallback invalid"
                )
                return False

            # Test agent fallback
            agent_fallback = integration._get_fallback_response("agent")
            if len(agent_fallback) < 10:
                self.log_test("Fallback Responses", "FAIL", "Agent fallback too short")
                return False

            # Test general fallback
            general_fallback = integration._get_fallback_response("general")
            if len(general_fallback) < 10:
                self.log_test(
                    "Fallback Responses", "FAIL", "General fallback too short"
                )
                return False

            self.log_test("Fallback Responses", "PASS", "All fallback types working")
            return True

        except Exception as e:
            self.log_test("Fallback Responses", "FAIL", str(e))
            return False

    def test_recovery(self) -> bool:
        """Test recovery after circuit breaker reset."""
        print("\n🔧 Testing Recovery...")

        try:
            # Reset circuit breaker
            OpenAIIntegration._failure_count = 0
            OpenAIIntegration._circuit_open = False
            OpenAIIntegration._circuit_open_until = None

            integration = OpenAIIntegration()

            # Test that API calls work after reset
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].message.content = "Recovery successful"

            with patch.object(
                integration.client.chat.completions,
                "create",
                return_value=mock_response,
            ):
                result = integration.generate_text("Test recovery")

                if result == "Recovery successful":
                    self.log_test("Recovery", "PASS", "API calls working after reset")
                    return True
                else:
                    self.log_test("Recovery", "FAIL", f"Unexpected result: {result}")
                    return False

        except Exception as e:
            self.log_test("Recovery", "FAIL", str(e))
            return False

    def run_all_tests(self) -> dict:
        """Run all API error tests."""
        print("🚀 Starting API Error Handling Test Suite\n")
        print("=" * 60)

        # Run tests
        self.test_results["502_handling"] = self.test_502_error_handling()
        self.test_results["retry_logic"] = self.test_retry_logic()
        self.test_results["circuit_breaker"] = self.test_circuit_breaker()
        self.test_results["fallback_responses"] = self.test_fallback_responses()
        self.test_results["recovery"] = self.test_recovery()

        # Generate summary
        self.generate_test_summary()

        return self.test_results

    def generate_test_summary(self):
        """Generate test summary report."""
        print("\n" + "=" * 60)
        print("🎯 API ERROR HANDLING TEST SUMMARY")
        print("=" * 60)

        passed_tests = sum(1 for result in self.test_results.values() if result)
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests) * 100

        print(
            f"📊 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})"
        )
        print()

        # Test details
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")

        if self.errors:
            print("\n🚨 ERRORS ENCOUNTERED:")
            for error in self.errors:
                print(f"   • {error}")

        print("\n" + "=" * 60)

        if success_rate >= 80:
            print("🎉 EXCELLENT: Error handling is robust!")
        elif success_rate >= 60:
            print("⚠️  GOOD: Error handling is mostly working")
        else:
            print("❌ POOR: Error handling needs improvement")

        print("=" * 60)


def main():
    """Main test execution function."""
    try:
        # Change to project directory
        os.chdir(project_root)

        # Run test suite
        test_suite = APIErrorTestSuite()
        results = test_suite.run_all_tests()

        # Exit with appropriate code
        success_rate = (
            sum(1 for result in results.values() if result) / len(results) * 100
        )
        exit_code = 0 if success_rate >= 80 else 1

        print(f"\n🏁 Test execution completed. Exit code: {exit_code}")
        return exit_code

    except Exception as e:
        print(f"❌ CRITICAL ERROR: Test suite failed to run: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
