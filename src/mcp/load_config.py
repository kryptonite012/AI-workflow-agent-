import json
import pathlib
from typing import List, Optional, Union

from src.mcp.mcp_register_structure import (
    ServerConfig,
    Command,
)  # Import Command from correct location


def load_mcp_configs():
    """Load and register MCP configurations."""
    from src.mcp.manager import MCP_Manager

    try:
        config_loader = McpConfigFile()
        server_configs = config_loader.retrieve_config()

        if server_configs:
            for config in server_configs:
                MCP_Manager.add_server(
                    name=config.name,
                    runner=config.command,
                    package=None,  # No package parameter for these configs
                    args=config.args,
                    func=config.wrapper,
                )
        return True
    except Exception as e:
        print(f"Failed to load MCP configs: {e}")
        return False


class McpConfigFile:
    __config_path: Union[str | pathlib.Path]

    @property
    def config_path(self) -> str:
        return self.__config_path

    @config_path.setter
    def config_path(self, value: str):
        self.__config_path = value

    @classmethod
    def __load(cls):
        """Load the MCP configuration from the specified file."""
        from src.config import settings
        from pathlib import Path

        if not hasattr(cls, "__config_path") or cls.__config_path is None:
            cls.__config_path = settings.MCP_CONFIG.get(
                "MCP_CONFIG_PATH"
            )  # Default path if not set
        try:
            if not Path.exists(Path(cls.__config_path).resolve()):
                raise FileNotFoundError(
                    f"Configuration file '{cls.__config_path}' does not exist."
                )
            with Path(cls.__config_path).open("r") as file:
                config_data = file.read()
            return config_data
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Configuration file '{cls.__config_path}' not found."
            )
        except Exception as e:
            raise Exception(f"An error occurred while loading the configuration: {e}")

    # File: load_config.py
    @classmethod
    def retrieve_config(cls) -> Optional[List[ServerConfig]]:
        """Parse .mcp.md.json into ServerConfig list"""
        from src.tools.lggraph_tools.wrappers.mcp_wrapper.uni_mcp_wrappers import (
            UniversalMCPWrapper,
        )

        content = cls.__load()

        if content:
            try:
                config = json.loads(content)
                servers_dict = config.get("servers", {})

                if not servers_dict:
                    raise ValueError("No servers found in configuration")

                server_configs = []
                for name, server_data in servers_dict.items():
                    server_config = ServerConfig(
                        name=name,
                        command=Command(
                            server_data.get("command", "npx")
                        ),  # Convert to Command enum
                        args=server_data.get("args", []),
                        env=server_data.get("env", {}),
                        wrapper=UniversalMCPWrapper,
                    )
                    server_configs.append(server_config)

                return server_configs

            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")

        return None
