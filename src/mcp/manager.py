import json
import os
import subprocess
from typing import Any, Callable, Optional

from src.config import settings
from src.mcp.dynamically_tool_register import DynamicToolRegister
from src.mcp.mcp_register_structure import (
    ServerConfig,
    Command,
    MPC_TOOL_SERVER_MAPPING,
)

# ✅ Structured Debug Helpers
from src.ui.diagnostics.debug_helpers import (
    debug_info,
    debug_warning,
    debug_error,
)

# 🎨 Rich Traceback Integration
from src.ui.diagnostics.rich_traceback_manager import (
    RichTracebackManager,
    rich_exception_handler,
)
import pathlib


class MCP_Manager:
    instance = None
    # mcp.md configs
    mcp_enabled = None
    mcp_servers: dict[str, ServerConfig] = {}
    running_servers: dict[str, subprocess.Popen] = {}
    response_id = 0

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self):
        self._initialize()

    @classmethod
    def generate_response_id(cls) -> int:
        """
        Generate a unique response ID for each request.
        :return: Unique response ID.
        """
        MCP_Manager.response_id += 1
        return MCP_Manager.response_id

    @classmethod
    def add_server(
        cls,
        name: str,
        runner: Command,
        package: Optional[str],
        args: list[str],
        func: Callable,
    ):
        """
        Add a server to the MCP manager.
        :param name: Name of the server.
        :param runner: Reference to the runner (e.g., uvx, npx).
        :param package: Command to run the server.
        :param args: List of arguments for the command.
        :param func: To assign the function to the llm's tools
        """

        """
        Example of mcp_servers dict with current structure:
        mcp_servers = {
            "name_of_server1": {
                "runner": "uvx",
                "package": "python server1.py",
                "args": ["--port", "8080"],
                "status": "stopped"
            },
            "name_of_server2": {
                "runner": "npx",
                "package": "python server2.py",
                "args": ["--host", "localhost", "--port", "9090"],
                "status": "stopped"
            }
        }
        """
        # MCP_Manager.mcp_servers[name] = {
        #     "runner": runner,
        #     "package": package,
        #     "args": args,
        #     "status": "stopped",  # Initial status of the server
        #     "func": func  # Function to handle server operations \
        #                   # (function that is associated with the server to handle its responses and make requests) \
        #                   # to assign the function to the llm's tools.
        # }

        # Filter out None package to avoid None in args array
        server_args = args if package is None else [package] + args

        MCP_Manager.mcp_servers[name] = ServerConfig(
            name=name,
            command=runner,
            args=server_args,  # Use filtered args
            env={},
            wrapper=func,
            status="stopped",
            pid=None,
        )
        debug_info(
            heading="MCP • SERVER_ADDED",
            body=f"Registered server '{name}' (runner={runner})",
            metadata={"package": package, "args": args},
        )

    @classmethod
    def tool_discovery(cls, mcp_server_name: str) -> Any:
        """
        :param mcp_server_name: Name of the MCP server to discover tools from.
        :return: Dictionary of discovered tools from the specified MCP server.
        """
        if mcp_server_name not in cls.mcp_servers:
            debug_warning(
                heading="MCP • TOOL_DISCOVERY_MISSED",
                body="Requested tool discovery on unknown server",
                metadata={"server": mcp_server_name},
            )
            return {}

        tool_discovery_request = {
            "jsonrpc": "2.0",
            "id": MCP_Manager.generate_response_id(),
            "method": "tools/list",
            "params": {},
        }

        try:
            proc = MCP_Manager.running_servers[mcp_server_name]
            proc.stdin.write(json.dumps(tool_discovery_request) + "\n")
            proc.stdin.flush()

            # 🔧 ENHANCED: Robust response reading with encoding handling
            try:
                response_line = proc.stdout.readline().strip()
                if not response_line:
                    debug_warning(
                        heading="MCP • TOOL_DISCOVERY_EMPTY_RESPONSE",
                        body="Server returned empty response for tools/list",
                        metadata={"server": mcp_server_name},
                    )
                    return {}

                # Handle potential encoding issues with multiple fallback strategies
                if isinstance(response_line, bytes):
                    # Try multiple encoding strategies for robust handling
                    for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
                        try:
                            response_line = response_line.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # Final fallback: decode with error replacement
                        response_line = response_line.decode("utf-8", errors="replace")
                        debug_warning(
                            heading="MCP • TOOL_DISCOVERY_ENCODING_FALLBACK",
                            body="Used encoding fallback with character replacement",
                            metadata={"server": mcp_server_name},
                        )
                elif isinstance(response_line, str):
                    # Already a string, but might have encoding issues
                    try:
                        # Test if string is properly encoded by trying to encode/decode
                        response_line.encode("utf-8")
                    except UnicodeEncodeError:
                        # Re-encode with error handling
                        response_line = response_line.encode(
                            "utf-8", errors="replace"
                        ).decode("utf-8")
                        debug_warning(
                            heading="MCP • TOOL_DISCOVERY_STRING_ENCODING_FIX",
                            body="Fixed string encoding issues",
                            metadata={"server": mcp_server_name},
                        )

                response_line_json = json.loads(response_line)

            except UnicodeDecodeError as encoding_error:
                debug_error(
                    heading="MCP • TOOL_DISCOVERY_ENCODING_ERROR",
                    body=f"All encoding strategies failed: {encoding_error}",
                    metadata={"server": mcp_server_name},
                )
                return {}
            except json.JSONDecodeError as json_error:
                debug_error(
                    heading="MCP • TOOL_DISCOVERY_JSON_ERROR",
                    body=f"JSON parsing failed: {json_error}",
                    metadata={
                        "server": mcp_server_name,
                        "response_preview": str(response_line),
                    },
                )
                return {}

            # 🔧 ENHANCED: Handle different response formats and error cases
            if "error" in response_line_json:
                error_info = response_line_json["error"]
                error_code = error_info.get("code", "unknown")
                error_message = error_info.get("message", "unknown error")

                debug_warning(
                    heading="MCP • TOOL_DISCOVERY_SERVER_ERROR",
                    body=f"Server returned error: {error_message} (code: {error_code})",
                    metadata={
                        "server": mcp_server_name,
                        "error_code": error_code,
                        "error_message": error_message,
                        "full_error": str(error_info),
                    },
                )

                # For git server, this might be normal - just continue without tools
                if mcp_server_name == "git" and error_code == -32602:
                    debug_info(
                        heading="MCP • GIT_SERVER_PROTOCOL_ISSUE",
                        body="Git server has different protocol requirements, continuing without tools",
                        metadata={"server": mcp_server_name},
                    )

                return {}

            ### main successful path
            if (
                "result" in response_line_json
                and "tools" in response_line_json["result"]
            ):
                tools_found = response_line_json["result"]["tools"]
                debug_info(
                    heading="MCP • TOOLS_DISCOVERED",
                    body=f"Discovered {len(tools_found)} tools",
                    metadata={
                        "server": mcp_server_name,
                        "tools": [t.get("name", "unnamed") for t in tools_found],
                    },
                )
                if tools_found:
                    DynamicToolRegister.register_tool(
                        response_line_json,
                        MCP_Manager.mcp_servers[mcp_server_name].get("wrapper"),
                    )
                else:
                    debug_warning(
                        heading="MCP • NO_TOOLS",
                        body="Server returned empty tool list",
                        metadata={"server": mcp_server_name},
                    )
            else:
                debug_error(
                    heading="MCP • INVALID_TOOL_RESPONSE",
                    body="Server returned unexpected tools/list format",
                    metadata={
                        "server": mcp_server_name,
                        "response_preview": str(response_line_json),
                    },
                )
            return response_line_json

        except Exception as discovery_error:
            debug_error(
                heading="MCP • TOOL_DISCOVERY_EXCEPTION",
                body=f"Tool discovery failed with exception: {discovery_error}",
                metadata={
                    "server": mcp_server_name,
                    "error_type": type(discovery_error).__name__,
                    "error_message": str(discovery_error)[:200],
                },
            )
            return {}

    @classmethod
    @rich_exception_handler("MCP Server Startup")
    def start_server(cls, name: str):
        """
        Start a server by its name.
        :param name: Name of the server to start.
        """
        try:
            if name in MCP_Manager.mcp_servers:
                server_info = MCP_Manager.mcp_servers[name]
                runner = server_info["command"]
                args = server_info.get("args", [])

                # 🔧 DEBUG: Add comprehensive debugging
                debug_info(
                    heading="MCP • DEBUG_SERVER_START",
                    body=f"Starting server '{name}' with detailed debug info",
                    metadata={
                        "server": name,
                        "runner": str(runner),
                        "runner_type": str(type(runner)),
                        "runner_value": getattr(runner, "value", "NO_VALUE_ATTR"),
                        "args": str(args),
                        "args_type": str(type(args)),
                    },
                )

                # Convert Command enum to its string value
                try:
                    if hasattr(runner, "value"):
                        command_str = runner.value
                    else:
                        command_str = str(runner)

                    command = [command_str] + args

                    debug_info(
                        heading="MCP • DEBUG_COMMAND_ARRAY",
                        body=f"Command array created for '{name}'",
                        metadata={
                            "command_str": command_str,
                            "command_array": str(command),
                            "first_element": str(command[0]) if command else "EMPTY",
                            "first_element_type": str(type(command[0]))
                            if command
                            else "EMPTY",
                        },
                    )

                except Exception as cmd_error:
                    debug_error(
                        heading="MCP • DEBUG_COMMAND_ERROR",
                        body=f"Error creating command for '{name}': {cmd_error}",
                        metadata={"server": name, "runner": str(runner)},
                    )
                    return False

                # Check working directory
                try:
                    working_dir = str(settings.BASE_DIR.parent.resolve())
                    debug_info(
                        heading="MCP • DEBUG_WORKING_DIR",
                        body=f"Working directory for '{name}': {working_dir}",
                        metadata={
                            "server": name,
                            "working_dir": working_dir,
                            "base_dir": str(settings.BASE_DIR),
                            "parent_exists": pathlib.Path(working_dir).exists(),
                        },
                    )
                except Exception as wd_error:
                    debug_error(
                        heading="MCP • DEBUG_WORKING_DIR_ERROR",
                        body=f"Error getting working directory: {wd_error}",
                        metadata={"server": name},
                    )
                    return False

                try:
                    # 🔧 FIX: Set proper encoding for subprocess communication
                    server_process = subprocess.Popen(
                        command,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE,
                        text=True,
                        encoding="utf-8",  # Explicitly set UTF-8 encoding
                        errors="replace",  # Handle encoding errors gracefully
                        bufsize=1,
                        cwd=working_dir,
                        env=os.environ.copy(),
                    )
                    MCP_Manager.running_servers[name] = server_process
                    server_info["status"] = "running"

                    debug_info(
                        heading="MCP • SERVER_PROCESS_STARTED",
                        body=f"Successfully started process for '{name}'",
                        metadata={
                            "server": name,
                            "pid": server_process.pid,
                            "command": str(command),
                            "working_dir": working_dir,
                        },
                    )

                    # Handshake / initialize
                    try:
                        init_request = {
                            "jsonrpc": "2.0",
                            "id": MCP_Manager.generate_response_id(),
                            "method": "initialize",
                            "params": {
                                "protocolVersion": "2024-11-05",
                                "capabilities": {},
                                "clientInfo": {
                                    "name": "langgraph-mcp.md-client",
                                    "version": "1.0.0",
                                },
                            },
                        }
                        server_process.stdin.write(json.dumps(init_request) + "\n")
                        server_process.stdin.flush()
                        init_response = server_process.stdout.readline()
                        debug_info(
                            heading="MCP • SERVER_INITIALIZED",
                            body=f"Handshake completed for '{name}'",
                            metadata={"init_response_preview": init_response[:120]},
                        )
                        # Discover tools
                        try:
                            tools = cls.tool_discovery(name)
                            if tools and "result" in tools:
                                # map discovered tools to server
                                MPC_TOOL_SERVER_MAPPING.update(
                                    {
                                        tool["name"]: name
                                        for tool in tools["result"]["tools"]
                                    }
                                )  # working
                            else:
                                debug_warning(
                                    heading="MCP • DISCOVERY_EMPTY",
                                    body="No tools returned after discovery",
                                    metadata={"server": name},
                                )
                        except Exception as tool_discovery_error:
                            RichTracebackManager.handle_exception(
                                tool_discovery_error,
                                context=f"MCP Tool Discovery - {name}",
                                extra_context={
                                    "server_name": name,
                                    "init_response": str(init_response),
                                },
                            )
                            debug_error(
                                heading="MCP • DISCOVERY_ERROR",
                                body=f"Tool discovery failed: {tool_discovery_error}",
                                metadata={"server": name},
                            )
                    except Exception as init_error:
                        RichTracebackManager.handle_exception(
                            init_error,
                            context=f"MCP Server Initialization - {name}",
                            extra_context={
                                "server_name": name,
                                "command": str(command),
                                "process_id": server_process.pid,
                            },
                        )
                        debug_warning(
                            heading="MCP • INIT_FAILED",
                            body=f"Initialization failed: {init_error}",
                            metadata={"server": name},
                        )

                    debug_info(
                        heading="MCP • SERVER_STARTED",
                        body=f"Started server '{name}'",
                        metadata={"args": args},
                    )
                    return True

                except subprocess.CalledProcessError as process_error:
                    RichTracebackManager.handle_exception(
                        process_error,
                        context=f"MCP Server Process Creation - {name}",
                        extra_context={
                            "command": str(command),
                            "server_name": name,
                            "runner": runner,
                        },
                    )
                    debug_error(
                        heading="MCP • PROCESS_ERROR",
                        body=f"Command failed: {process_error}",
                        metadata={"server": name, "command": str(command)},
                    )
                    return False
                except Exception as e:
                    RichTracebackManager.handle_exception(
                        e,
                        context=f"MCP Server Startup - {name}",
                        extra_context={
                            "server_name": name,
                            "command": str(command),
                            "runner": runner,
                        },
                    )
                    debug_error(
                        heading="MCP • STARTUP_ERROR",
                        body=f"Failed to start server: {e}",
                        metadata={"server": name},
                    )
                    return False
            else:
                debug_error(
                    heading="MCP • UNKNOWN_SERVER",
                    body="Attempted to start non-existent server",
                    metadata={"server": name},
                )
                return False
        except Exception as e:
            RichTracebackManager.handle_exception(
                e,
                context=f"MCP Server Startup Wrapper - {name}",
                extra_context={"server_name": name},
            )
            debug_error(
                heading="MCP • CRITICAL_START_ERROR",
                body=f"Critical error starting server: {e}",
                metadata={"server": name},
            )
            return False

    def _initialize(self):
        """
        Initialize the MCP manager.
        This method checks the MCP_ENABLED setting and performs any necessary setup.
        :return: True if MCP is enabled, False otherwise.
        """
        # Perform any necessary initialization here
        MCP_Manager.mcp_enabled = settings.MCP_CONFIG.get("MCP_ENABLED")
        debug_info(
            heading="MCP • MANAGER_INIT",
            body="MCP Manager initialized",
            metadata={"enabled": bool(MCP_Manager.mcp_enabled)},
        )
        return MCP_Manager.mcp_enabled

    @classmethod
    def call_mcp_server(
        cls, name: str, tool_name: str, args: dict
    ) -> Optional[dict[str, Any]]:
        """
        Call a specific MCP server by its name with additional arguments.
        :param name: Name of the server to call.
        :param tool_name: Name of the tool to call on the server.
        :param args: Additional arguments to pass to the server.
        :return: Structured response dict with success/error status, or None for critical failures.
        """
        # Check if server exists and is running
        if name not in MCP_Manager.mcp_servers:
            msg = f"Server '{name}' not found"
            debug_error(heading="MCP • CALL_ERROR", body=msg, metadata={"server": name})
            return {"success": False, "error": msg}
        if MCP_Manager.mcp_servers[name]["status"] != "running":
            msg = f"Server '{name}' is not running"
            debug_error(heading="MCP • CALL_ERROR", body=msg, metadata={"server": name})
            return {"success": False, "error": msg}
        debug_info(
            heading="MCP • TOOL_CALL",
            body=f"Calling tool '{tool_name}'",
            metadata={"server": name, "args": args},
        )
        proc = MCP_Manager.running_servers.get(name)
        if not proc:
            msg = f"Server '{name}' process not found"
            debug_error(heading="MCP • CALL_ERROR", body=msg, metadata={"server": name})
            return {"success": False, "error": msg}
        try:
            mcp_request = {
                "jsonrpc": "2.0",
                "id": MCP_Manager.generate_response_id(),
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": args},
            }
            proc.stdin.write(json.dumps(mcp_request) + "\n")
            proc.stdin.flush()

            # 🔧 FIX: Robust response reading with encoding handling
            try:
                response_line = proc.stdout.readline().strip()
                if not response_line:
                    msg = f"No response from server '{name}'"
                    debug_error(
                        heading="MCP • CALL_ERROR", body=msg, metadata={"server": name}
                    )
                    return {"success": False, "error": msg}

                # Handle potential encoding issues with multiple fallback strategies
                if isinstance(response_line, bytes):
                    # Try multiple encoding strategies for robust handling
                    for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
                        try:
                            response_line = response_line.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # Final fallback: decode with error replacement
                        response_line = response_line.decode("utf-8", errors="replace")
                        debug_warning(
                            heading="MCP • CALL_ENCODING_FALLBACK",
                            body="Used encoding fallback with character replacement for tool call",
                            metadata={"server": name, "tool": tool_name},
                        )
                elif isinstance(response_line, str):
                    # Already a string, but might have encoding issues
                    try:
                        # Test if string is properly encoded by trying to encode/decode
                        response_line.encode("utf-8")
                    except UnicodeEncodeError:
                        # Re-encode with error handling
                        response_line = response_line.encode(
                            "utf-8", errors="replace"
                        ).decode("utf-8")
                        debug_warning(
                            heading="MCP • CALL_STRING_ENCODING_FIX",
                            body="Fixed string encoding issues in tool call response",
                            metadata={"server": name, "tool": tool_name},
                        )

            except UnicodeDecodeError as encoding_error:
                msg = f"Encoding error reading response: {encoding_error}"
                debug_error(
                    heading="MCP • CALL_ENCODING_ERROR",
                    body=msg,
                    metadata={"server": name, "tool": tool_name},
                )
                return {"success": False, "error": msg}

            try:
                json_response = json.loads(response_line)
                if "error" in json_response:
                    msg = f"MCP server error: {json_response['error']}"
                    debug_error(
                        heading="MCP • TOOL_ERROR",
                        body=msg,
                        metadata={"server": name, "tool": tool_name},
                    )
                    return {"success": False, "error": msg}
                if "result" in json_response:
                    debug_info(
                        heading="MCP • TOOL_SUCCESS",
                        body="Tool executed successfully",
                        metadata={"server": name, "tool": tool_name},
                    )
                    return {"success": True, "data": json_response["result"]}
                debug_warning(
                    heading="MCP • NO_RESULT_FIELD",
                    body="Response missing 'result' field; returning raw payload",
                    metadata={"server": name, "tool": tool_name},
                )
                return {"success": True, "data": json_response}
            except json.JSONDecodeError as e:
                msg = f"Invalid JSON response: {e}"
                debug_error(
                    heading="MCP • PARSE_ERROR",
                    body=msg,
                    metadata={"server": name, "tool": tool_name},
                )
                return {"success": False, "error": msg, "raw_response": response_line}
        except Exception as e:
            msg = f"Communication error: {e}"
            debug_error(
                heading="MCP • COMM_ERROR",
                body=msg,
                metadata={"server": name, "tool": tool_name},
            )
            return {"success": False, "error": msg}

    @classmethod
    def stop_server(cls, name: str) -> bool:
        """
        Stop a specific server by its name.
        :param name: Name of the server to stop.
        :return: True if server was stopped successfully, False otherwise.
        """
        if name not in cls.running_servers:
            debug_warning(
                heading="MCP • STOP_IGNORED",
                body="Stop requested for server not running",
                metadata={"server": name},
            )
            return False
        proc = cls.running_servers[name]
        try:
            proc.terminate()
            proc.wait(timeout=5)
            del cls.running_servers[name]
            cls.mcp_servers[name]["status"] = "stopped"
            debug_info(
                heading="MCP • SERVER_STOPPED",
                body="Server stopped successfully",
                metadata={"server": name},
            )
            return True
        except Exception as e:
            debug_error(
                heading="MCP • STOP_ERROR",
                body=f"Failed to stop server: {e}",
                metadata={"server": name},
            )
            return False

    @classmethod
    def stop_all_servers(cls) -> bool:
        """
        Stop all running MCP servers. Safe for cleanup - doesn't fail on errors.
        :return: True if all servers were stopped, False if any failed.
        """
        if not cls.running_servers:
            debug_info(
                heading="MCP • STOP_ALL_SKIP",
                body="No running servers to stop",
                metadata={},
            )
            return True
        success = True
        for server_name in list(cls.running_servers.keys()):
            try:
                if not cls.stop_server(server_name):
                    success = False
            except Exception as e:
                debug_error(
                    heading="MCP • STOP_ALL_ERROR",
                    body=f"Exception stopping '{server_name}': {e}",
                    metadata={"server": server_name},
                )
                success = False
        if success:
            debug_info(
                heading="MCP • STOP_ALL_COMPLETE",
                body="All servers stopped",
                metadata={},
            )
        else:
            debug_warning(
                heading="MCP • STOP_ALL_PARTIAL",
                body="Some servers failed to stop",
                metadata={},
            )
        return success

    @classmethod
    def cleanup(cls):
        """
        Cleanup method for ChatDestructor integration.
        Stops all servers and handles any cleanup errors gracefully.
        """
        try:
            cls.stop_all_servers()
        except Exception as e:
            debug_error(
                heading="MCP • CLEANUP_ERROR", body=f"Cleanup failed: {e}", metadata={}
            )

    @classmethod
    def read_uri_resource(cls, server_name : str, uri_resource)-> dict[str, Any] | None:
        """ Read a URI resource from a specific MCP server.
        :param server_name: Name of the MCP server to read from.
        :param uri_resource: The URI resource to read.
        :return: Structured response dict with success/error status, or None for critical failures.
        """

        if server_name not in cls.mcp_servers:
            msg = f"Server '{server_name}' not found"
            debug_error(heading="MCP • URI_READ_ERROR", body=msg, metadata={"server": server_name})
            return {"success": False, "error": msg}
        if MCP_Manager.mcp_servers[server_name]["status"] != "running":
            msg = f"Server '{server_name}' is not running"
            debug_error(heading="MCP • URI_READ_ERROR", body=msg, metadata={"server": server_name})
            return {"success": False, "error": msg}
        debug_info(
            heading="MCP • URI_READ",
            body=f"Reading URI resource '{uri_resource}'",
            metadata={"server": server_name, "uri": uri_resource},
        )
        proc = MCP_Manager.running_servers.get(server_name)
        if not proc:
            msg = f"Server '{server_name}' process not found"
            debug_error(heading="MCP • URI_READ_ERROR", body=msg, metadata={"server": server_name})
            return {"success": False, "error": msg}
        try:
            mcp_uri_read_request = {
                "jsonrpc": "2.0",
                "id": MCP_Manager.generate_response_id(),
                "method": "resources/read",
                "params": {"uri": uri_resource},
            }
            proc.stdin.write(json.dumps(mcp_uri_read_request) + "\n")
            proc.stdin.flush()
            # 🔧 FIX: Robust response reading with encoding handling
            try:
                response_line = proc.stdout.readline().strip()
                if not response_line:
                    msg = f"No response from server '{server_name}'"
                    debug_error(
                        heading="MCP • URI_READ_ERROR", body=msg, metadata={"server": server_name}
                    )
                    return {"success": False, "error": msg}

                # Handle potential encoding issues with multiple fallback strategies
                if isinstance(response_line, bytes):
                    # Try multiple encoding strategies for robust handling
                    for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
                        try:
                            response_line = response_line.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # Final fallback: decode with error replacement
                        response_line = response_line.decode("utf-8", errors="replace")
                        debug_warning(
                            heading="MCP • URI_READ_ENCODING_FALLBACK",
                            body="Used encoding fallback with character replacement for URI read",
                            metadata={"server": server_name, "uri": uri_resource},
                        )
                elif isinstance(response_line, str):
                    # Already a string, but might have encoding issues
                    try:
                        # Test if string is properly encoded by trying to encode/decode
                        response_line.encode("utf-8")
                    except UnicodeEncodeError:
                        # Re-encode with error handling
                        response_line = response_line.encode(
                            "utf-8", errors="replace"
                        ).decode("utf-8")
                        debug_warning(
                            heading="MCP • URI_READ_STRING_ENCODING_FIX",
                            body="Fixed string encoding issues in URI read response",
                            metadata={"server": server_name, "uri": uri_resource},
                        )
            except UnicodeDecodeError as encoding_error:
                msg = f"Encoding error reading response: {encoding_error}"
                debug_error(
                    heading="MCP • URI_READ_ENCODING_ERROR",
                    body=msg,
                    metadata={"server": server_name, "uri": uri_resource},
                )
                return {"success": False, "error": msg}
            try:
                json_response = json.loads(response_line)
                if "error" in json_response:
                    msg = f"MCP server error: {json_response['error']}"
                    debug_error(
                        heading="MCP • URI_READ_TOOL_ERROR",
                        body=msg,
                        metadata={"server": server_name, "uri": uri_resource},
                    )
                    return {"success": False, "error": msg}
                ## pass main successful response
                if "result" in json_response:
                    debug_info(
                        heading="MCP • URI_READ_SUCCESS",
                        body="URI resource read successfully",
                        metadata={"server": server_name, "uri": uri_resource},
                    )
                    return {"success": True, "data": json_response["result"]}
                debug_warning(
                    heading="MCP • URI_READ_NO_RESULT_FIELD",
                    body="Response missing 'result' field; returning raw payload",
                    metadata={"server": server_name, "uri": uri_resource},
                )
                # return full response if no result field
                return {"success": True, "data": json_response}
            except json.JSONDecodeError as e:
                msg = f"Invalid JSON response: {e}"
                debug_error(
                    heading="MCP • URI_READ_PARSE_ERROR",
                    body=msg,
                    metadata={"server": server_name, "uri": uri_resource},
                )
                return {"success": False, "error": msg, "raw_response": response_line}
        except Exception as e:
            msg = f"Communication error: {e}"
            debug_error(
                heading="MCP • URI_READ_COMM_ERROR",
                body=msg,
                metadata={"server": server_name, "uri": uri_resource},
            )
            return {"success": False, "error": msg}