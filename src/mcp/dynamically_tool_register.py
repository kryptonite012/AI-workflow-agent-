import inspect

from src.tools.lggraph_tools.tool_assign import ToolAssign


class DynamicToolRegister:
    """
    A class to dynamically register tools in the MCP (Multi-Channel Processing) system along with their input schema.
    This class is designed to be used as a singleton, ensuring that only one instance
    exists throughout the application.
    """

    _instance = None
    mcp_running_servers = []
    tool_list = []  # List to hold registered tools that going to being appended in the tool_assign at the chat initializer

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DynamicToolRegister, cls).__new__(cls)
            cls._instance.tools = []
        return cls._instance

    @classmethod
    def register_tool(cls, response, function):
        """
        Extracts the schema from the response and registers MCP tools dynamically.

        :param response: The response object from the MCP server of tools/list.
        :param function: The function to be associated with the tool.
        """
        # get the tool's schema from the response
        tools = response["result"]["tools"]
        if not tools:
            raise ValueError("No tools found in the response")

        try:
            for tool in tools:
                tool_name = tool["name"]
                arguments = tool["inputSchema"]

                # Add tool name to arguments schema (modify the properties' dict)
                if not isinstance(arguments, dict):
                    raise ValueError("Input schema must be a dictionary")
                if "properties" not in arguments:
                    arguments["properties"] = {}
                    # Ensure tool name is not already in properties

                arguments["properties"]["tool_name"] = {
                    "type": "string",
                    # "description": f"The MCP tool name to execute.",
                    # 'title': 'Tool Name',
                    "default": tool_name,  # Provide default value
                    # "example": tool_name  # Example value for clarity
                }
                if "tool_name" not in arguments["properties"]:
                    pass
                # now add the tool name to the required list
                if "required" not in arguments:
                    arguments["required"] = []
                if "tool_name" not in arguments["required"]:
                    # arguments['required'].append('tool_name')
                    pass

                # get the description of the tool
                description = (
                    f"{tool['description']} \n"
                    # f"**Usage:** Provide all required arguments: {', '.join(arguments.get('required', []))}. "
                    # f"Set `tool_name` to `{tool_name}` to select this tool."
                )

                # log the tool registration
                # settings.socket_con.send_error(f"[DEBUG] Registering tool: {tool_name} with description: {description}")
                # settings.socket_con.send_error(f"[DEBUG] Tool arguments schema: {arguments}")

                # register the tool with its schema
                DynamicToolRegister.tool_list.append(
                    ToolAssign(
                        name=tool_name,
                        description=description,
                        func=function,  # Function to be called when this tool is invoked
                        args_schema=arguments,  # Keep as dict - tool_selector.py handles this
                    )
                )

        except KeyError as e:
            raise ValueError(f"Invalid response format: {e}")
        except Exception as e:
            raise ValueError(f"Error registering tool: {e} {inspect.trace()}")

    @classmethod
    def get_registered_tools(cls):
        """
        Get the list of dynamically registered MCP tools.

        :return: List of ToolAssign instances for MCP tools
        """
        return cls.tool_list

    @classmethod
    def clear_tools(cls):
        """
        Clear all registered tools. Useful for testing or reinitialization.
        """
        cls.tool_list.clear()

    @classmethod
    def get_tool_count(cls):
        """
        Get the count of registered MCP tools.

        :return: Number of registered tools
        """
        return len(cls.tool_list)

    def get_tools(self):
        """Returns the list of registered tools (instance method for compatibility)."""
        return self.tools
