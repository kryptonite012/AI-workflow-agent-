#!/usr/bin/env python3
"""
Simple test to check what MCP servers are already configured.
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


def check_existing_mcp_servers():
    """Check what MCP servers are already configured."""
    print("🔍 Checking existing MCP server configurations...")

    try:
        from src.mcp.manager import MCP_Manager

        # Initialize MCP Manager
        mcp_manager = MCP_Manager()

        print(f"📊 Configured servers: {len(MCP_Manager.mcp_servers)}")

        for server_name, server_config in MCP_Manager.mcp_servers.items():
            print(f"   {server_name}: {type(server_config)} - {server_config}")

        if not MCP_Manager.mcp_servers:
            print("⚠️ No servers configured. Need to manually add servers.")

            # Let's manually add the servers we know work from the error log
            from src.tools.lggraph_tools.wrappers.mcp_wrapper.uni_mcp_wrappers import (
                UniversalMCPWrapper,
            )
            from src.mcp.mcp_register_structure import Command

            # Add servers based on the error log
            servers_to_add = [
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

            for name, runner, args in servers_to_add:
                MCP_Manager.add_server(
                    name=name,
                    runner=runner,
                    package=None,
                    args=args,
                    func=UniversalMCPWrapper,
                )
                print(f"   ✅ Added {name} server")

            print(f"📊 Now configured servers: {len(MCP_Manager.mcp_servers)}")

        return len(MCP_Manager.mcp_servers) > 0

    except Exception as e:
        print(f"❌ Failed to check MCP servers: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_server_startup():
    """Test starting the configured servers."""
    print("\n🚀 Testing server startup...")

    try:
        from src.mcp.manager import MCP_Manager

        startup_results = {}

        for server_name in list(MCP_Manager.mcp_servers.keys())[
            :3
        ]:  # Test first 3 servers only
            print(f"   Starting {server_name}...")
            try:
                result = MCP_Manager.start_server(server_name)
                startup_results[server_name] = result
                if result:
                    print(f"   ✅ {server_name} started successfully")
                else:
                    print(f"   ❌ {server_name} failed to start")
            except Exception as e:
                print(f"   ❌ {server_name} failed with error: {e}")
                startup_results[server_name] = False

        return startup_results

    except Exception as e:
        print(f"❌ Server startup test failed: {e}")
        import traceback

        traceback.print_exc()
        return {}


if __name__ == "__main__":
    print("🔬 MCP Server Configuration Test")
    print("=" * 40)

    # Check existing servers
    servers_exist = check_existing_mcp_servers()

    if servers_exist:
        # Test startup
        startup_results = test_server_startup()

        success_count = sum(1 for result in startup_results.values() if result)
        print(
            f"\n📊 Startup Results: {success_count}/{len(startup_results)} servers started"
        )

        if success_count > 0:
            print("✅ MCP server system is working!")
        else:
            print("⚠️ No servers started, but configuration is present")
    else:
        print("❌ No MCP servers configured")

    print("\nTest completed.")
