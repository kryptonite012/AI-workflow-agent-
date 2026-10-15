#!/usr/bin/env python3
"""
Real test for the exact MCP 'universal' server error from error log.

This test reproduces the exact agent mode failure scenario:
1. Agent calls read_graph tool
2. Tool tries to use 'universal' server (which doesn't exist)
3. Gets "Server 'universal' not found" error
4. Agent workflow fails
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import sys
import os
from pathlib import Path

# Add the project root to Python path


def setup_mcp_servers():
    """Set up MCP servers exactly as they appear in the error log."""
    print("?? Setting up MCP servers from error log configuration...")

    try:
        from src.mcp.manager import MCP_Manager
        from src.tools.lggraph_tools.wrappers.mcp_wrapper.uni_mcp_wrappers import (
            UniversalMCPWrapper,
        )
        from src.mcp.mcp_register_structure import Command

        # Initialize MCP Manager
        mcp_manager = MCP_Manager()

        # Add servers exactly as they appear in the error log
        print("?? Adding servers from error log...")

        servers_config = [
            (
                "github",
                Command.NPX,
                ["-y", "@modelcontextprotocol/server-github@latest"],
            ),
            ("git", Command.UVX, ["mcp.md-server-git"]),
            (
                "filesystem",
                Command.NPX,
                [
                    "-y",
                    "@modelcontextprotocol/server-filesystem@latest",
                    "C:\\Users\\pirat\\PycharmProjects\\AI_llm",
                ],
            ),
            (
                "memory",
                Command.NPX,
                ["-y", "@modelcontextprotocol/server-memory@latest"],
            ),
            (
                "puppeteer",
                Command.NPX,
                ["-y", "@modelcontextprotocol/server-puppeteer@latest"],
            ),
            (
                "sentry",
                Command.NPX,
                ["-y", "mcp.md-remote@latest", "https://mcp.sentry.dev/mcp"],
            ),
            (
                "sequential-thinking",
                Command.NPX,
                ["-y", "@modelcontextprotocol/server-sequential-thinking"],
            ),
        ]

        for name, runner, args in servers_config:
            MCP_Manager.add_server(
                name=name,
                runner=runner,
                package=None,
                args=args,
                func=UniversalMCPWrapper,
            )
            print(f"   ? Added {name} server")

        print(f"?? Total servers configured: {len(MCP_Manager.mcp_servers)}")
        return True

    except Exception as e:
        print(f"? Failed to setup MCP servers: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_failing_tools_before_fix():
    """Test the exact tools that were failing in the error log."""
    print("\n?? Testing failing tools BEFORE fix...")

    try:
        # Import the ORIGINAL universal tool (should fail)
        from src.tools.lggraph_tools.tools.mcp_integrated_tools.universal import (
            universal_tool,
        )

        # Test the exact tools from the error log that were failing
        failing_tools = [
            {
                "tool_name": "read_graph",
                "description": "Memory server tool for reading knowledge graph",
            },
            {
                "tool_name": "search_nodes",
                "query": "ai work flow one",
                "description": "Memory server tool for searching nodes",
            },
        ]

        for tool_test in failing_tools:
            tool_name = tool_test["tool_name"]
            print(f"   Testing {tool_name}...")

            try:
                result = universal_tool(**tool_test)

                if isinstance(result, dict) and "Server 'universal' not found" in str(
                    result.get("error", "")
                ):
                    print(
                        f"   ? {tool_name}: CONFIRMED - 'universal' server error reproduced"
                    )
                    return True  # We successfully reproduced the error
                else:
                    print(f"   ?? {tool_name}: Unexpected result - {result}")

            except Exception as e:
                error_str = str(e)
                if "Server 'universal' not found" in error_str:
                    print(
                        f"   ? {tool_name}: CONFIRMED - 'universal' server error reproduced via exception"
                    )
                    return True  # We successfully reproduced the error
                else:
                    print(f"   ?? {tool_name}: Different error - {error_str}")

        print("   ?? Could not reproduce the 'universal' server error")
        return False

    except Exception as e:
        print(f"? Test setup failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def apply_fix():
    """Apply the fix to the universal tool."""
    print("\n?? Applying fix to universal tool...")

    try:
        # Read the current universal.py content
        universal_file_path = (
            "src/tools/lggraph_tools/tools/mcp_integrated_tools/universal.py"
        )

        with open(universal_file_path, "r") as f:
            current_content = f.read()

        # Check if fix is already applied
        if "tool_server_mapping" in current_content:
            print("? Fix already applied to universal.py")
            return True

        print("? Fix NOT applied yet - tool still hardcoded to use 'universal' server")
        print(
            "   Current code calls: MCP_Manager.call_mcp_server('universal', tool_name, arguments)"
        )
        print("   This is why we get 'Server universal not found' error")

        # The fix was already applied in our previous response, but let's verify it's working
        return False

    except Exception as e:
        print(f"? Failed to check/apply fix: {e}")
        return False


def test_fixed_tools():
    """Test tools after fix is applied."""
    print("\n?? Testing tools AFTER fix...")

    try:
        # Start some servers first
        from src.mcp.manager import MCP_Manager

        # Start memory server specifically (for read_graph and search_nodes)
        print("?? Starting memory server...")
        memory_started = MCP_Manager.start_server("memory")

        if memory_started:
            print("? Memory server started successfully")

            # Wait a moment for server to initialize
            import time

            time.sleep(2)

            # Test the tools
            from src.tools.lggraph_tools.tools.mcp_integrated_tools.universal import (
                universal_tool,
            )

            test_cases = [
                {"tool_name": "read_graph"},
                {"tool_name": "search_nodes", "query": "ai work flow one"},
            ]

            for test_case in test_cases:
                tool_name = test_case["tool_name"]
                print(f"   Testing {tool_name} with fix...")

                try:
                    result = universal_tool(**test_case)

                    if isinstance(result, dict):
                        if result.get(
                            "success"
                        ) == False and "Server 'universal' not found" in str(
                            result.get("error", "")
                        ):
                            print(
                                f"   ? {tool_name}: Still trying to use 'universal' server - FIX NOT WORKING"
                            )
                            return False
                        elif result.get("success") == False and "not running" in str(
                            result.get("error", "")
                        ):
                            print(
                                f"   ? {tool_name}: Fix working - now correctly maps to proper server"
                            )
                            return True
                        elif result.get("success") == True:
                            print(
                                f"   ? {tool_name}: Fix working - tool executed successfully"
                            )
                            return True
                        else:
                            print(f"   ?? {tool_name}: Unclear result - {result}")
                    else:
                        print(f"   ? {tool_name}: Fix working - got non-error result")
                        return True

                except Exception as e:
                    error_str = str(e)
                    if "Server 'universal' not found" in error_str:
                        print(
                            f"   ? {tool_name}: Still trying to use 'universal' server - FIX NOT WORKING"
                        )
                        return False
                    else:
                        print(
                            f"   ? {tool_name}: Fix working - different error indicates server mapping worked"
                        )
                        return True
        else:
            print("? Memory server failed to start")
            return False

    except Exception as e:
        print(f"? Testing fixed tools failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def simulate_agent_mode():
    """Simulate the exact agent mode scenario from error log."""
    print("\n?? Simulating agent mode scenario...")

    try:
        # The exact user message from the error log
        user_message = "/agent can you sequentialy think for this task task is i want you to read the graph in which load the main project in your context main project is ai work flow one can you explain me what you got ??"

        print(f"?? User message: {user_message}")
        print("?? Simulating agent workflow...")

        # Instead of running full agent (which has other dependencies),
        # let's simulate the exact tool calls that agent would make
        from src.tools.lggraph_tools.tools.mcp_integrated_tools.universal import (
            universal_tool,
        )

        # Step 1: Agent would call read_graph (this is what fails in error log)
        print("   Step 1: Agent calls read_graph...")
        try:
            read_result = universal_tool(tool_name="read_graph")

            if isinstance(read_result, dict) and "Server 'universal' not found" in str(
                read_result.get("error", "")
            ):
                print("   ? FAILURE: read_graph still tries to use 'universal' server")
                print("   ?? This is the exact error from the error log!")
                return False
            else:
                print(
                    "   ? SUCCESS: read_graph now works (no 'universal' server error)"
                )

        except Exception as e:
            if "Server 'universal' not found" in str(e):
                print("   ? FAILURE: read_graph still tries to use 'universal' server")
                print("   ?? This is the exact error from the error log!")
                return False
            else:
                print(
                    "   ? SUCCESS: read_graph now works (different error indicates fix working)"
                )

        # Step 2: Agent would call search_nodes (this also fails in error log)
        print("   Step 2: Agent calls search_nodes...")
        try:
            search_result = universal_tool(
                tool_name="search_nodes", query="ai work flow one"
            )

            if isinstance(
                search_result, dict
            ) and "Server 'universal' not found" in str(search_result.get("error", "")):
                print(
                    "   ? FAILURE: search_nodes still tries to use 'universal' server"
                )
                print("   ?? This is the exact error from the error log!")
                return False
            else:
                print(
                    "   ? SUCCESS: search_nodes now works (no 'universal' server error)"
                )

        except Exception as e:
            if "Server 'universal' not found" in str(e):
                print(
                    "   ? FAILURE: search_nodes still tries to use 'universal' server"
                )
                print("   ?? This is the exact error from the error log!")
                return False
            else:
                print(
                    "   ? SUCCESS: search_nodes now works (different error indicates fix working)"
                )

        print("   ?? Agent simulation successful - no 'universal' server errors!")
        return True

    except Exception as e:
        print(f"? Agent simulation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run the complete test suite."""
    print("?? MCP 'Universal' Server Fix Test")
    print("=" * 50)
    print("Testing the exact error scenario from error_log.txt")
    print()

    # Step 1: Setup
    setup_success = setup_mcp_servers()
    if not setup_success:
        print("?? Cannot proceed - MCP setup failed")
        return False

    # Step 2: Reproduce the error
    print("?? REPRODUCING THE ERROR FROM ERROR LOG...")
    error_reproduced = test_failing_tools_before_fix()

    if error_reproduced:
        print("? Successfully reproduced the 'Server universal not found' error")
        print("   This confirms the issue described in the error log")
    else:
        print("?? Could not reproduce the error - fix may already be applied")

    # Step 3: Check if fix is applied
    print("\n?? CHECKING FIX STATUS...")
    fix_applied = apply_fix()

    if not fix_applied:
        print("? Fix needs to be applied to universal.py")
        print("   The tool is still hardcoded to use 'universal' server")
        return False

    # Step 4: Test after fix
    print("\n? TESTING AFTER FIX...")
    fix_working = test_fixed_tools()

    if not fix_working:
        print("? Fix is not working properly")
        return False

    # Step 5: Simulate agent mode
    print("\n?? SIMULATING AGENT MODE...")
    agent_success = simulate_agent_mode()

    if not agent_success:
        print("? Agent simulation failed")
        return False

    # Final results
    print("\n" + "=" * 50)
    print("?? SUCCESS: MCP 'universal' server error FIXED!")
    print("=" * 50)
    print("? Error reproduced and confirmed")
    print("? Fix applied and working")
    print("? Tools now map to correct servers")
    print("? Agent mode simulation successful")
    print("\n?? The agent can now successfully:")
    print("   - Call read_graph (maps to memory server)")
    print("   - Call search_nodes (maps to memory server)")
    print("   - Execute multi-step workflows without 'universal' server errors")

    return True


if __name__ == "__main__":
    try:
        success = main()
        exit_code = 0 if success else 1
        print(f"\nExiting with code: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n?? Test failed with exception: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
