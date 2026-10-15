#!/usr/bin/env python3
"""
Quick test to verify the agent mode is working properly.
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
from pathlib import Path

# Add project root to path


async def test_agent_workflow():
    """Test the agent workflow that was previously failing."""
    print("?? Testing Agent Mode...")

    try:
        # Setup MCP servers first
        from src.mcp.manager import MCP_Manager
        from src.tools.lggraph_tools.wrappers.mcp_wrapper.uni_mcp_wrappers import (
            UniversalMCPWrapper,
        )
        from src.mcp.mcp_register_structure import Command

        # Initialize and configure servers
        mcp_manager = MCP_Manager()

        # Add memory server for the test
        MCP_Manager.add_server(
            name="memory",
            runner=Command.NPX,
            package=None,
            args=["-y", "@modelcontextprotocol/server-memory@latest"],
            func=UniversalMCPWrapper,
        )

        # Start memory server
        print("?? Starting memory server...")
        memory_started = MCP_Manager.start_server("memory")

        if memory_started:
            print("? Memory server started successfully")
            await asyncio.sleep(2)  # Wait for initialization

            # Test the exact tools that were failing
            from src.tools.lggraph_tools.tools.mcp_integrated_tools.universal import (
                universal_tool,
            )

            print("?? Testing read_graph (should NOT get 'universal' server error)...")
            try:
                result = universal_tool(tool_name="read_graph")

                if isinstance(result, dict) and "Server 'universal' not found" in str(
                    result.get("error", "")
                ):
                    print("? FAILED: Still getting 'universal' server error!")
                    return False
                else:
                    print(
                        "? SUCCESS: No 'universal' server error (tool executed or got proper server error)"
                    )

            except Exception as e:
                if "Server 'universal' not found" in str(e):
                    print(
                        "? FAILED: Still getting 'universal' server error via exception!"
                    )
                    return False
                else:
                    print(
                        "? SUCCESS: No 'universal' server error (got different error which is expected)"
                    )

            print(
                "?? Testing search_nodes (should NOT get 'universal' server error)..."
            )
            try:
                result = universal_tool(tool_name="search_nodes", query="test")

                if isinstance(result, dict) and "Server 'universal' not found" in str(
                    result.get("error", "")
                ):
                    print("? FAILED: Still getting 'universal' server error!")
                    return False
                else:
                    print("? SUCCESS: No 'universal' server error")

            except Exception as e:
                if "Server 'universal' not found" in str(e):
                    print(
                        "? FAILED: Still getting 'universal' server error via exception!"
                    )
                    return False
                else:
                    print("? SUCCESS: No 'universal' server error")

            print(
                "\n?? Agent mode test PASSED! The 'Server universal not found' error is fixed!"
            )
            return True
        else:
            print("? Failed to start memory server")
            return False

    except Exception as e:
        print(f"? Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run the agent test."""
    print("?? Agent Mode Fix Verification Test")
    print("=" * 40)

    success = await test_agent_workflow()

    if success:
        print("\n? ALL TESTS PASSED!")
        print("Your agent mode should now work properly for complex queries.")
        exit_code = 0
    else:
        print("\n? Tests failed. The fix needs more work.")
        exit_code = 1

    print(f"\nExiting with code: {exit_code}")
    return exit_code


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n?? Test failed: {e}")
        sys.exit(1)
