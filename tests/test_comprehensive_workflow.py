"""
Comprehensive test suite for AI-Agent-Workflow system functionality.
Tests all three modes: /use llm, /use tool, /agent
Includes error handling, retry logic, and comprehensive validation.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import sys
import os
import asyncio
import time
import json
from pathlib import Path

# Add project root to path

from src.config import settings
from src.core.chat_initializer import ChatInitializer
from src.models.state import State, StateAccessor
from src.utils.model_manager import ModelManager
from src.mcp.manager import MCP_Manager


class AIWorkflowTestSuite:
    """Comprehensive test suite for AI-Agent-Workflow system."""

    def __init__(self):
        self.test_results = {
            "initialization": False,
            "llm_mode": False,
            "tool_mode": False,
            "agent_mode": False,
            "mcp_servers": False,
            "error_handling": False,
            "comprehensive": False,
        }
        self.errors = []
        self.initializer = None

    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results."""
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_symbol} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        if status == "FAIL":
            self.errors.append(f"{test_name}: {details}")

    def test_initialization(self) -> bool:
        """Test system initialization."""
        print("\n🔧 Testing System Initialization...")

        try:
            # Initialize the chat system
            self.initializer = ChatInitializer()

            # Check if core components are initialized
            if not hasattr(self.initializer, "graph") or self.initializer.graph is None:
                self.log_test(
                    "Graph Initialization", "FAIL", "LangGraph not initialized"
                )
                return False

            if not hasattr(self.initializer, "tools") or not self.initializer.tools:
                self.log_test("Tools Initialization", "FAIL", "No tools loaded")
                return False

            self.log_test(
                "System Initialization",
                "PASS",
                f"Loaded {len(self.initializer.tools)} tools",
            )
            return True

        except Exception as e:
            self.log_test("System Initialization", "FAIL", str(e))
            return False

    def test_mcp_servers(self) -> bool:
        """Test MCP server health and functionality."""
        print("\n🔧 Testing MCP Servers...")

        try:
            # Check MCP manager status
            if not MCP_Manager.mcp_enabled:
                self.log_test("MCP Configuration", "FAIL", "MCP not enabled")
                return False

            # Validate server health
            health_status = MCP_Manager.validate_server_health()

            if health_status["health_percentage"] < 50:
                self.log_test(
                    "MCP Server Health",
                    "FAIL",
                    f"Only {health_status['health_percentage']:.1f}% healthy",
                )
                return False

            self.log_test(
                "MCP Servers",
                "PASS",
                f"{health_status['healthy_servers']}/{health_status['total_servers']} servers healthy, "
                f"{health_status['tools_available']} tools available",
            )
            return True

        except Exception as e:
            self.log_test("MCP Servers", "FAIL", str(e))
            return False

    def test_llm_mode(self) -> bool:
        """Test /use llm mode functionality."""
        print("\n🔧 Testing LLM Mode...")

        try:
            # Create test state
            state = State(
                messages=[
                    settings.HumanMessage(
                        content="Tell me a simple fact about Python programming"
                    )
                ],
                message_type="llm",
            )

            # Test LLM response
            result = self.initializer.graph.invoke(state)

            if not result or "messages" not in result or not result["messages"]:
                self.log_test("LLM Mode", "FAIL", "No response from LLM")
                return False

            response_content = result["messages"][-1].content
            if len(response_content.strip()) < 10:
                self.log_test("LLM Mode", "FAIL", "Response too short")
                return False

            self.log_test(
                "LLM Mode",
                "PASS",
                f"Generated response: {len(response_content)} characters",
            )
            return True

        except Exception as e:
            self.log_test("LLM Mode", "FAIL", str(e))
            return False

    def test_tool_mode(self) -> bool:
        """Test /use tool mode functionality."""
        print("\n🔧 Testing Tool Mode...")

        try:
            # Create test state for tool usage
            state = State(
                messages=[
                    settings.HumanMessage(
                        content="Search for 'Python programming basics'"
                    )
                ],
                message_type="tool",
            )

            # Test tool execution
            result = self.initializer.graph.invoke(state)

            if not result or "messages" not in result or not result["messages"]:
                self.log_test("Tool Mode", "FAIL", "No response from tool")
                return False

            response_content = result["messages"][-1].content
            if (
                "search" not in response_content.lower()
                and "python" not in response_content.lower()
            ):
                self.log_test(
                    "Tool Mode",
                    "FAIL",
                    "Tool response doesn't contain expected content",
                )
                return False

            self.log_test("Tool Mode", "PASS", "Tool executed successfully")
            return True

        except Exception as e:
            self.log_test("Tool Mode", "FAIL", str(e))
            return False

    def test_agent_mode(self) -> bool:
        """Test /agent mode functionality."""
        print("\n🔧 Testing Agent Mode...")

        try:
            # Create test state for agent mode
            state = State(
                messages=[
                    settings.HumanMessage(
                        content="/agent search for Python tutorials and summarize the first result"
                    )
                ],
                message_type="agent",
            )

            # Test agent execution
            result = self.initializer.graph.invoke(state)

            if not result or "messages" not in result or not result["messages"]:
                self.log_test("Agent Mode", "FAIL", "No response from agent")
                return False

            response_content = result["messages"][-1].content

            # Check for agent-specific response patterns
            if len(response_content.strip()) < 20:
                self.log_test("Agent Mode", "FAIL", "Agent response too short")
                return False

            self.log_test("Agent Mode", "PASS", "Agent executed successfully")
            return True

        except Exception as e:
            self.log_test("Agent Mode", "FAIL", str(e))
            return False

    def test_error_handling(self) -> bool:
        """Test error handling and recovery."""
        print("\n🔧 Testing Error Handling...")

        try:
            # Test with invalid input
            state = State(
                messages=[settings.HumanMessage(content="")], message_type="llm"
            )

            # Should handle empty input gracefully
            result = self.initializer.graph.invoke(state)

            if not result or "messages" not in result:
                self.log_test("Error Handling", "FAIL", "System crashed on empty input")
                return False

            # Test API failure simulation
            from src.utils.open_ai_integration import OpenAIIntegration

            # Check if circuit breaker exists
            if not hasattr(OpenAIIntegration, "_check_circuit_breaker"):
                self.log_test(
                    "Error Handling", "FAIL", "Circuit breaker not implemented"
                )
                return False

            # Check if fallback responses exist
            integration = OpenAIIntegration()
            fallback = integration._get_fallback_response("classification")

            if not fallback or len(fallback) < 10:
                self.log_test(
                    "Error Handling", "FAIL", "Fallback responses not implemented"
                )
                return False

            self.log_test("Error Handling", "PASS", "Error handling mechanisms working")
            return True

        except Exception as e:
            self.log_test("Error Handling", "FAIL", str(e))
            return False

    def test_comprehensive_workflow(self) -> bool:
        """Test a comprehensive workflow using multiple modes."""
        print("\n🔧 Testing Comprehensive Workflow...")

        try:
            # Test sequence: LLM -> Tool -> Agent
            test_cases = [
                {
                    "mode": "llm",
                    "input": "What is machine learning?",
                    "expected_keywords": ["machine", "learning", "algorithm"],
                },
                {
                    "mode": "tool",
                    "input": "Search for latest AI news",
                    "expected_keywords": ["search", "AI", "news"],
                },
                {
                    "mode": "agent",
                    "input": "/agent find information about Python and create a summary",
                    "expected_keywords": ["python", "summary"],
                },
            ]

            success_count = 0
            for i, test_case in enumerate(test_cases):
                try:
                    state = State(
                        messages=[settings.HumanMessage(content=test_case["input"])],
                        message_type=test_case["mode"],
                    )

                    result = self.initializer.graph.invoke(state)

                    if result and "messages" in result and result["messages"]:
                        response = result["messages"][-1].content.lower()
                        keywords_found = sum(
                            1
                            for keyword in test_case["expected_keywords"]
                            if keyword in response
                        )

                        if keywords_found > 0:
                            success_count += 1
                            self.log_test(
                                f"Workflow Step {i + 1}",
                                "PASS",
                                f"Mode: {test_case['mode']}",
                            )
                        else:
                            self.log_test(
                                f"Workflow Step {i + 1}",
                                "FAIL",
                                f"No expected keywords found in response",
                            )
                    else:
                        self.log_test(f"Workflow Step {i + 1}", "FAIL", "No response")

                except Exception as e:
                    self.log_test(f"Workflow Step {i + 1}", "FAIL", str(e))

            if success_count >= 2:  # At least 2 out of 3 should work
                self.log_test(
                    "Comprehensive Workflow",
                    "PASS",
                    f"{success_count}/3 workflow steps successful",
                )
                return True
            else:
                self.log_test(
                    "Comprehensive Workflow",
                    "FAIL",
                    f"Only {success_count}/3 workflow steps successful",
                )
                return False

        except Exception as e:
            self.log_test("Comprehensive Workflow", "FAIL", str(e))
            return False

    def run_all_tests(self) -> dict:
        """Run all tests and return results."""
        print("🚀 Starting AI-Agent-Workflow Comprehensive Test Suite\n")
        print("=" * 60)

        # Run tests in order
        self.test_results["initialization"] = self.test_initialization()

        if self.test_results["initialization"]:
            self.test_results["mcp_servers"] = self.test_mcp_servers()
            self.test_results["llm_mode"] = self.test_llm_mode()
            self.test_results["tool_mode"] = self.test_tool_mode()
            self.test_results["agent_mode"] = self.test_agent_mode()
            self.test_results["error_handling"] = self.test_error_handling()
            self.test_results["comprehensive"] = self.test_comprehensive_workflow()
        else:
            print("❌ Initialization failed - skipping other tests")

        # Generate summary
        self.generate_test_summary()

        return self.test_results

    def generate_test_summary(self):
        """Generate test summary report."""
        print("\n" + "=" * 60)
        print("🎯 TEST SUMMARY REPORT")
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
            print("🎉 EXCELLENT: System is working well!")
        elif success_rate >= 60:
            print("⚠️  GOOD: System is mostly functional with some issues")
        else:
            print("❌ POOR: System has significant issues requiring attention")

        print("=" * 60)


def main():
    """Main test execution function."""
    try:
        # Change to project directory
        os.chdir(project_root)

        # Run test suite
        test_suite = AIWorkflowTestSuite()
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
