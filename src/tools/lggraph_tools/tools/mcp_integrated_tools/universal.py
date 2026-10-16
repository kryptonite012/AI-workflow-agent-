def universal_tool(**kwargs):
    """
    Universal tool for interacting with any MCP server.

    This function allows you to call any MCP server with the provided parameters.
    It abstracts the details of the MCP server interaction, making it easy to use.

    :param kwargs: Dynamic parameters that vary by MCP tool
    :return: Result from the specific MCP tool operation
    """
    from src.mcp.manager import MCP_Manager
    from src.ui.diagnostics.debug_helpers import (
        debug_info,
        debug_critical,
        debug_warning,
    )
    from src.mcp.mcp_register_structure import MPC_TOOL_SERVER_MAPPING

    # 🔧 FIX: Enhanced tool_name extraction with validation
    tool_name = kwargs.pop("tool_name", None)

    # Critical validation: tool_name must be provided
    if not tool_name or tool_name == "unknown tool":
        debug_critical(
            heading="MCP_UNIVERSAL • MISSING_TOOL_NAME",
            body="No valid tool_name provided - this will cause MCP server errors",
            metadata={
                "provided_tool_name": tool_name,
                "kwargs_keys": list(kwargs.keys()),
                "error_prevention": "returning_error_immediately",
            },
        )
        return {
            "success": False,
            "error": f"Invalid tool_name: '{tool_name}'. Tool name is required for MCP operations.",
            "available_tools": list(MPC_TOOL_SERVER_MAPPING.keys())[
                :10
            ],  # Show first 10 for reference
        }

    arguments = kwargs

    # 🔧 FIX: Enhanced tool-to-server mapping
    tool_server_mapping = {
        # Memory server tools (knowledge graph operations)
        "read_graph": "memory",
        "search_nodes": "memory",
        "open_nodes": "memory",
        "create_entities": "memory",
        "create_relations": "memory",
        "add_observations": "memory",
        "delete_entities": "memory",
        "delete_observations": "memory",
        "delete_relations": "memory",
        # GitHub server tools
        "create_or_update_file": "github",
        "search_repositories": "github",
        "create_repository": "github",
        "get_file_contents": "github",
        "push_files": "github",
        "create_issue": "github",
        "create_pull_request": "github",
        "fork_repository": "github",
        "create_branch": "github",
        "list_commits": "github",
        "list_issues": "github",
        "update_issue": "github",
        "add_issue_comment": "github",
        "search_code": "github",
        "search_issues": "github",
        "search_users": "github",
        "get_issue": "github",
        "get_pull_request": "github",
        "list_pull_requests": "github",
        "create_pull_request_review": "github",
        "merge_pull_request": "github",
        "get_pull_request_files": "github",
        "get_pull_request_status": "github",
        "update_pull_request_branch": "github",
        "get_pull_request_comments": "github",
        "get_pull_request_reviews": "github",
        # Filesystem server tools
        "read_file": "filesystem",
        "read_text_file": "filesystem",
        "read_media_file": "filesystem",
        "read_multiple_files": "filesystem",
        "write_file": "filesystem",
        "edit_file": "filesystem",
        "create_directory": "filesystem",
        "list_directory": "filesystem",
        "list_directory_with_sizes": "filesystem",
        "directory_tree": "filesystem",
        "move_file": "filesystem",
        "search_files": "filesystem",
        "get_file_info": "filesystem",
        "list_allowed_directories": "filesystem",
        # Puppeteer server tools
        "puppeteer_navigate": "puppeteer",
        "puppeteer_screenshot": "puppeteer",
        "puppeteer_click": "puppeteer",
        "puppeteer_fill": "puppeteer",
        "puppeteer_select": "puppeteer",
        "puppeteer_hover": "puppeteer",
        "puppeteer_evaluate": "puppeteer",
        # Sequential thinking server tools
        "sequentialthinking": "sequential-thinking",
    }

    # 🔧 FIX: Use both static and dynamic mapping for server resolution
    server_name = tool_server_mapping.get(tool_name) or MPC_TOOL_SERVER_MAPPING.get(
        tool_name
    )

    # Enhanced debugging with detailed mapping info
    debug_critical(
        heading="MCP_UNIVERSAL • DEBUG",
        body="Current tool-server mapping and running servers",
        metadata={
            "tool_server_mapping": tool_server_mapping,
            "dynamic_tool_server_mapping": MPC_TOOL_SERVER_MAPPING,
            "running_servers": list(MCP_Manager.running_servers.keys()),
            "requested_tool": tool_name,
            "server_name": server_name,
        },
    )

    if not server_name:
        debug_warning(
            heading="MCP_UNIVERSAL • UNKNOWN_TOOL",
            body=f"Tool '{tool_name}' not found in server mapping, attempting to find server",
            metadata={
                "tool_name": tool_name,
                "available_mappings": list(tool_server_mapping.keys()),
            },
        )

        # 🔧 FIX: Systematic fallback server detection
        fallback_servers = [
            "filesystem",
            "memory",
            "github",
            "puppeteer",
            "sequential-thinking",
        ]
        for server in fallback_servers:
            if server in MCP_Manager.running_servers:
                debug_info(
                    heading="MCP_UNIVERSAL • FALLBACK_ATTEMPT",
                    body=f"Trying server '{server}' as fallback for tool '{tool_name}'",
                    metadata={"tool_name": tool_name, "fallback_server": server},
                )

                # Test if server can handle this tool
                test_response = MCP_Manager.call_mcp_server(
                    server, tool_name, arguments
                )
                if test_response and test_response.get("success"):
                    server_name = server
                    debug_info(
                        heading="MCP_UNIVERSAL • FALLBACK_SUCCESS",
                        body=f"Server '{server}' accepted tool '{tool_name}'",
                        metadata={"tool_name": tool_name, "successful_server": server},
                    )
                    break

        if not server_name:
            error_msg = f"No server found for tool '{tool_name}'. Available servers: {list(MCP_Manager.running_servers.keys())}"
            debug_critical(
                heading="MCP_UNIVERSAL • NO_SERVER_FOUND",
                body=error_msg,
                metadata={
                    "tool_name": tool_name,
                    "running_servers": list(MCP_Manager.running_servers.keys()),
                    "static_mapping_keys": list(tool_server_mapping.keys())[:10],
                    "dynamic_mapping_keys": list(MPC_TOOL_SERVER_MAPPING.keys())[:10],
                },
            )
            return {"success": False, "error": error_msg}

    debug_info(
        heading="MCP_UNIVERSAL • TOOL_MAPPING",
        body=f"Calling tool '{tool_name}' on server '{server_name}'",
        metadata={
            "tool_name": tool_name,
            "server_name": server_name,
            "arguments": arguments,
        },
    )

    # 🔧 FIX: Enhanced error handling for MCP server calls
    try:
        response = MCP_Manager.call_mcp_server(server_name, tool_name, arguments)
    except Exception as call_error:
        debug_critical(
            heading="MCP_UNIVERSAL • SERVER_CALL_EXCEPTION",
            body=f"Exception calling MCP server: {call_error}",
            metadata={
                "tool_name": tool_name,
                "server_name": server_name,
                "error_type": type(call_error).__name__,
                "arguments": str(arguments)[:200],
            },
        )
        return {
            "success": False,
            "error": f"Server call failed: {str(call_error)}",
            "server": server_name,
            "tool": tool_name,
        }

    if response is None:
        debug_critical(
            heading="MCP_UNIVERSAL • ERROR",
            body="No response from MCP server",
            metadata={
                "tool_name": tool_name,
                "server_name": server_name,
                "arguments": arguments,
            },
        )
        return {"success": False, "error": "No response from MCP server"}

    if response.get("success"):
        # Extract the actual content from the structured response
        data = response.get("data")
        # handle for uri type response
        if isinstance(data, dict) and data.get('method') == 'notifications/resources/updated':
            uri = data.get('params', {}).get('uri')
            if uri:
                # now it is confirmed that it is uri ##
                debug_critical(
                    heading="MCP_UNIVERSAL • URI_DETECTED",
                    body=f"URI detected in MCP response: {uri}",
                    metadata={
                        "tool_name": tool_name,
                        "server_name": server_name,
                    },
                )
                resolved_uri = MCP_Manager.read_uri_resource(server_name, uri).get('data', None)
                if resolved_uri:
                    return resolved_uri
                else:
                    return {"success": False, "error": f"Failed to resolve URI: {uri}"}
            pass
        debug_info(
            heading="MCP_UNIVERSAL • SUCCESS",
            body="Response received from MCP server",
            metadata={
                "tool_name": tool_name,
                "server_name": server_name,
                "data_type": type(data).__name__,
                "has_content": "content" in data if isinstance(data, dict) else False,
            },
        )
        return data["content"] if isinstance(data, dict) and "content" in data else data
    else:
        # Handle error response
        error_msg = response.get("error", "Unknown error occurred")
        debug_info(
            heading="MCP_UNIVERSAL • ERROR",
            body=f"Error from MCP server: {error_msg}",
            metadata={
                "tool_name": tool_name,
                "server_name": server_name,
                "error_message": error_msg,
            },
        )
        return response
