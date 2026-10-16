    if selection.tool_name and selection.tool_name.lower() != "none":
        from src.tools.lggraph_tools.tool_response_manager import ToolResponseManager
        for tool in tools:
            if tool.name.lower() == selection.tool_name.lower():
                try:
                    # ?? FIX: Enhanced parameter preparation for tool execution
                    parameters.update({'tool_name': tool.name})  # Ensure tool_name is included in parameters
                    
                    # ?? FIX: Validate parameters before tool execution
                    if not isinstance(parameters, dict):
                        from src.ui.diagnostics.debug_helpers import debug_warning
                        debug_warning(
                            heading="TOOL_SELECTOR • INVALID_PARAMETERS",
                            body=f"Parameters should be dict, got {type(parameters).__name__}",
                            metadata={
                                "tool_name": tool.name,
                                "parameters_type": type(parameters).__name__,
                                "fallback_action": "creating_empty_dict"
                            }
                        )
                        parameters = {'tool_name': tool.name}
                    
                    # ?? FIX: Ensure tool_name is always present
                    if 'tool_name' not in parameters:
                        parameters['tool_name'] = tool.name
                        
                    from src.ui.diagnostics.debug_helpers import debug_info
                    debug_info(
                        heading="TOOL_SELECTOR • TOOL_EXECUTION",
                        body=f"Executing tool '{tool.name}' with validated parameters",
                        metadata={
                            "tool_name": tool.name,
                            "parameter_count": len(parameters),
                            "has_tool_name": 'tool_name' in parameters,
                            "context": "tool_selector_execution"
                        }
                    )
                    
                    tool.invoke(parameters)
                    result = ToolResponseManager().get_response()[
                        -1].content  # Get the last response from the tool manager
                    # Print tool result in modern style
                    print_message(result, sender="tool")