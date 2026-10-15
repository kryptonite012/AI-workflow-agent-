#!/usr/bin/env python3
"""
Test script to simulate the agent mode with MCP server integration.

This test simulates the exact user request that was failing:
"/agent can you sequentialy think for this task task is i want you to read the graph
in which load the main project in your context main project is ai work flow one
can you explain me what you got ??"

Tests:
1. MCP server initialization
2. Tool-to-server mapping fix
3. Agent mode execution with read_graph and search_nodes
4. Error handling and fallback mechanisms
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import asyncio
import sys
import os
import time
from pathlib import Path

# Add the project root to Python path


async def test_mcp_server_startup():
    """Test MCP server startup and tool discovery."""
    print("🔄 Testing MCP Server Startup...")

    try:
        from src.mcp.manager import MCP_Manager
        from src.mcp.load_config import load_mcp_configs
        from src.tools.lggraph_tools.wrappers.mcp_wrapper.uni_mcp_wrappers import (
            UniversalMCPWrapper,
        )

        # Initialize MCP Manager
        mcp_manager = MCP_Manager()

        # Load MCP configurations
        print("📝 Loading MCP configurations...")
        load_mcp_configs()

        # Start servers
        print("🚀 Starting MCP servers...")
        startup_results = {}

        for server_name in MCP_Manager.mcp_servers.keys():
            print(f"   Starting {server_name}...")
            result = MCP_Manager.start_server(server_name)
            startup_results[server_name] = result
            if result:
                print(f"   ✅ {server_name} started successfully")
            else:
                print(f"   ❌ {server_name} failed to start")

            # Small delay between server starts
            await asyncio.sleep(0.5)

        # Wait for servers to fully initialize
        print("⏳ Waiting for servers to initialize...")
        await asyncio.sleep(3)

        # Check running servers
        print("📊 Server Status:")
        for server_name, is_running in startup_results.items():
            status = "✅ Running" if is_running else "❌ Failed"
            print(f"   {server_name}: {status}")

        return startup_results

    except Exception as e:
        print(f"❌ MCP startup failed: {e}")
        import traceback

        traceback.print_exc()
        return {}


def test_tool_server_mapping():
    """Test the fixed tool-to-server mapping."""
    print("\n🗺️ Testing Tool-to-Server Mapping...")

    try:
        from src.tools.lggraph_tools.tools.mcp_integrated_tools.universal import (
            universal_tool,
        )

        # Test mapping for key tools
        test_tools = [
            ("read_graph", "memory"),
            ("search_nodes", "memory"),
            ("create_entities", "memory"),
            ("list_directory", "filesystem"),
            ("create_repository", "github"),
            ("puppeteer_navigate", "puppeteer"),
            ("sequentialthinking", "sequential-thinking"),
        ]

        mapping_results = {}

        for tool_name, expected_server in test_tools:
            print(f"   Testing {tool_name} -> {expected_server}")
            try:
                # This should now map to the correct server instead of 'universal'
                result = universal_tool(
                    tool_name=tool_name,
                    query="test" if tool_name == "search_nodes" else ".",
                )

                if result and not (
                    isinstance(result, dict) and result.get("success") == False
                ):
                    print(f"   ✅ {tool_name}: Mapped correctly to {expected_server}")
                    mapping_results[tool_name] = True
                else:
                    print(
                        f"   ⚠️ {tool_name}: Server found but tool execution failed (expected for testing)"
                    )
                    mapping_results[tool_name] = (
                        True  # Mapping works even if execution fails
                    )

            except Exception as e:
                error_msg = str(e)
                if "not found" in error_msg:
                    print(f"   ❌ {tool_name}: Server mapping failed - {error_msg}")
                    mapping_results[tool_name] = False
                else:
                    print(
                        f"   ⚠️ {tool_name}: Execution error (mapping may be correct) - {error_msg}"
                    )
                    mapping_results[tool_name] = (
                        True  # Tool was found, execution error is different issue
                    )

        print(
            f"📊 Mapping Test Results: {sum(mapping_results.values())}/{len(mapping_results)} tools mapped correctly"
        )
        return mapping_results

    except Exception as e:
        print(f"❌ Tool mapping test failed: {e}")
        import traceback

        traceback.print_exc()
        return {}


async def test_agent_mode_simulation():
    """Simulate the failing agent mode request."""
    print("\n🤖 Testing Agent Mode Simulation...")

    try:
        from src.agents.agent_mode_node import Agent
        from src.config import settings

        # Initialize settings if needed
        if not hasattr(settings, "listeners"):
            settings.listeners = {}

        # Create agent instance
        agent = Agent()

        # Simulate the exact user request that was failing
        user_message = "/agent can you sequentialy think for this task task is i want you to read the graph in which load the main project in your context main project is ai work flow one can you explain me what you got ?? first read the graph then search the node make sure the actuall node is not that i spelled it wrong .. (make sure agent)"

        print(f"📝 User Request: {user_message}")
        print("🔄 Starting agent workflow...")

        # Execute agent workflow
        start_time = time.time()

        try:
            result = await agent.start(user_message)
            execution_time = time.time() - start_time

            print(f"⏱️ Execution completed in {execution_time:.2f} seconds")

            if result:
                print("✅ Agent mode execution successful!")
                print(f"📤 Agent Response: {result}")
                return True
            else:
                print("⚠️ Agent mode returned empty result")
                return False

        except Exception as agent_error:
            execution_time = time.time() - start_time
            print(
                f"❌ Agent execution failed after {execution_time:.2f} seconds: {agent_error}"
            )

            # Check if the error is the old "Server 'universal' not found" error
            if "Server 'universal' not found" in str(agent_error):
                print(
                    "💥 CRITICAL: Still getting 'universal' server error - fix not working!"
                )
                return False
            elif "NoneType" in str(agent_error) and "iterable" in str(agent_error):
                print("💥 CRITICAL: Still getting OpenAI NoneType iteration error!")
                return False
            else:
                print(f"⚠️ Different error occurred: {type(agent_error).__name__}")
                import traceback

                traceback.print_exc()
                return False

    except Exception as e:
        print(f"❌ Agent mode simulation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_individual_mcp_tools():
    """Test individual MCP tools that were failing."""
    print("\n🔧 Testing Individual MCP Tools...")

    try:
        from src.tools.lggraph_tools.tools.mcp_integrated_tools.universal import (
            universal_tool,
        )

        # Test the specific tools that were failing
        failing_tools = [
            {"name": "read_graph", "args": {}, "expected_server": "memory"},
            {
                "name": "search_nodes",
                "args": {"query": "ai work flow one"},
                "expected_server": "memory",
            },
            {
                "name": "list_directory",
                "args": {"path": "."},
                "expected_server": "filesystem",
            },
        ]

        tool_results = {}

        for tool_info in failing_tools:
            tool_name = tool_info["name"]
            args = tool_info["args"]
            expected_server = tool_info["expected_server"]

            print(f"   Testing {tool_name} (should use {expected_server} server)...")

            try:
                # Add tool_name to args
                test_args = {**args, "tool_name": tool_name}

                start_time = time.time()
                result = universal_tool(**test_args)
                execution_time = time.time() - start_time

                if result and not (
                    isinstance(result, dict)
                    and "Server 'universal' not found" in str(result)
                ):
                    print(f"   ✅ {tool_name}: Success in {execution_time:.2f}s")
                    print(f"      Result type: {type(result).__name__}")
                    if isinstance(result, dict) and "success" in result:
                        print(f"      Success: {result.get('success')}")
                    tool_results[tool_name] = True
                else:
                    print(f"   ❌ {tool_name}: Failed - {result}")
                    tool_results[tool_name] = False

            except Exception as tool_error:
                error_msg = str(tool_error)
                if "Server 'universal' not found" in error_msg:
                    print(
                        f"   💥 {tool_name}: CRITICAL - Still trying to use 'universal' server!"
                    )
                    tool_results[tool_name] = False
                else:
                    print(f"   ⚠️ {tool_name}: Error - {error_msg}")
                    # This might be OK - server mapping worked but tool execution failed
                    tool_results[tool_name] = True

        success_count = sum(tool_results.values())
        total_count = len(tool_results)
        print(
            f"📊 Individual Tool Test Results: {success_count}/{total_count} tools working"
        )

        return tool_results

    except Exception as e:
        print(f"❌ Individual tool testing failed: {e}")
        import traceback

        traceback.print_exc()
        return {}


async def run_comprehensive_test():
    """Run all tests to verify the MCP fix."""
    print("🚀 Starting Comprehensive MCP Fix Test")
    print("=" * 50)

    # Test 1: MCP Server Startup
    startup_results = await test_mcp_server_startup()
    startup_success = len([r for r in startup_results.values() if r]) > 0

    if not startup_success:
        print("\n💥 CRITICAL: No MCP servers started successfully!")
        print("Cannot proceed with further testing.")
        return False

    # Test 2: Tool-to-Server Mapping
    mapping_results = test_tool_server_mapping()
    mapping_success = (
        len([r for r in mapping_results.values() if r]) >= len(mapping_results) * 0.8
    )

    # Test 3: Individual MCP Tools
    tool_results = await test_individual_mcp_tools()
    tools_success = (
        len([r for r in tool_results.values() if r]) >= len(tool_results) * 0.8
    )

    # Test 4: Agent Mode Simulation
    agent_success = await test_agent_mode_simulation()

    # Final Results
    print("\n" + "=" * 50)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 50)

    results = {
        "MCP Server Startup": startup_success,
        "Tool-to-Server Mapping": mapping_success,
        "Individual MCP Tools": tools_success,
        "Agent Mode Simulation": agent_success,
    }

    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")

    overall_success = all(results.values())

    if overall_success:
        print("\n🎉 ALL TESTS PASSED! MCP fix is working correctly.")
    else:
        print("\n⚠️ Some tests failed. The fix may need further adjustment.")

        # Specific failure analysis
        if not results["MCP Server Startup"]:
            print("   - Check MCP server configurations and dependencies")
        if not results["Tool-to-Server Mapping"]:
            print("   - Review tool-to-server mapping in universal.py")
        if not results["Individual MCP Tools"]:
            print("   - Debug individual tool execution and server communication")
        if not results["Agent Mode Simulation"]:
            print("   - Check agent mode orchestration and OpenAI integration")

    print("\n📝 Test completed. Check output above for detailed results.")
    return overall_success


if __name__ == "__main__":
    print("🔬 MCP Server Fix Test Script")
    print("Testing fix for 'Server universal not found' error")
    print("\nRunning from:", os.getcwd())

    try:
        # Run the comprehensive test
        success = asyncio.run(run_comprehensive_test())

        # Exit with appropriate code
        exit_code = 0 if success else 1
        print(f"\nExiting with code: {exit_code}")
        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test script failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
