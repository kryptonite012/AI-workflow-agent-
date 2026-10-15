import json


def get_tool_argument_schema(tool):
    """
    Returns the JSON schema for the tool's argument structure.

    This function inspects the `args_schema` attribute of a tool instance to determine its type and returns a JSON schema string that describes the expected arguments for that tool.

    - If `tool.args_schema` is a Pydantic model, it uses the model's `model_json_schema()` method to generate a standards-compliant JSON schema for validation and documentation.
    - If `tool.args_schema` is a raw Python `dict` (as used by some MCP tools), it serializes the dictionary directly, assuming it already represents a valid JSON schema.
    - If `tool.args_schema` is neither a Pydantic model nor a dictionary, the function returns a default empty object schema, indicating that no specific arguments are required.

    :param tool: The tool object whose argument schema should be retrieved.
    :return: JSON string representing the tool's argument schema.
    """
    if hasattr(tool.args_schema, "model_json_schema"):
        # Pydantic model - use model_json_schema()
        return json.dumps(tool.args_schema.model_json_schema())
    elif isinstance(tool.args_schema, dict):
        # Raw dict (from MCP tools) - use directly
        return json.dumps(tool.args_schema)
    else:
        # Fallback for unknown types
        return json.dumps({"type": "object", "properties": {}})
