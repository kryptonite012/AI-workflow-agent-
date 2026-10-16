from langchain_core.tools.structured import StructuredTool
from typing import List, ClassVar


class ToolAssign(StructuredTool):
    tool_list: ClassVar[List["ToolAssign"]] = []

    def __init__(self, name: str, description: str, func=None, args_schema=None):
        """
        Initialize the ToolAssign with a name and description.

        :param name: The name of the tool.
        :param description: A brief description of what the tool does.
        """
        super().__init__(
            name=name, description=description, function=func, args_schema=args_schema
        )
        self.name = name
        self.description = description
        self.func = func
        self.args_schema = args_schema

    @classmethod
    def set_tools_list(cls, tools_list: list):
        """
        Set the list of tools available for selection.

        :param tools_list: List of tool instances to be used in the tool selection process.
        """
        ToolAssign._tool_list = tools_list

    @classmethod
    def get_tools_list(cls):
        """
        Get the list of tools available for selection.

        :return: List of tool instances.
        """
        return cls._tool_list

    @classmethod
    def append_tools_list(cls, tools: List["ToolAssign"]):
        """
        Append a new tool to the existing list of tools.

        :param tools: The tool instance to be added.
        """
        if cls._tool_list is None:
            cls._tool_list = tools
        cls._tool_list.extend(tools)
