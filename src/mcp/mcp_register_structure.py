from typing import TypedDict, List, Callable, Optional
from enum import Enum


class Command(str, Enum):
    # package manager or command to run the server
    NPX = "npx"
    UVX = "uvx"
    PIPX = "pipx"
    PIP = "pip"
    PYTHON = "python"


class ServerConfig(TypedDict):
    name: str
    command: Command
    # package: str   ## e.g ("@modelcontextprotocol/server-github@latest")  now package would be included in the args of that mcp.md
    args: List[str]
    env: dict[str, str]
    wrapper: Callable
    status: Optional[str]  # e.g., "running", "stopped"
    pid: Optional[int]  # Process ID if the server is running


MPC_TOOL_SERVER_MAPPING: dict[str, str] = {}  # key: tool_name, value: server_name
