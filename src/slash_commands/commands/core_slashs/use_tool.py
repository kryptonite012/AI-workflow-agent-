"""
this is routing slash command to use a specific tool
todo we can also implement option here like :-
[CommandOption(name="tool_name", description="Name of the tool to use"), CommandOption(name="input", description="Input for the tool")]
"""
from src.slash_commands.on_run_time_register import OnRunTimeRegistry
from src.slash_commands.protocol import SlashCommand, CommandResult, CommandOption


def register_slash_command_use_tool():
    use_tool_command = SlashCommand(
        command="tool",
        options=None,
        requirements=None,
        description="Use a specific tool with given input.",
        handler=use_tool_handler
    )
    registry = OnRunTimeRegistry()
    try:
        registry.register(use_tool_command)
    except registry.CommandAlreadyRegisteredError:
        # Command is already registered; we can choose to log this or ignore it.
        pass


def use_tool_handler(command: SlashCommand, options: CommandOption | None) -> CommandResult:
    """Handler function to use a specific tool with given input.

    :param command: The SlashCommand object for use_tool
    :param options: CommandOption for use_tool command flags, or None
    :return: CommandResult indicating success or failure of the operation.
    """
    try:
        # Here you would implement the actual logic to use the specified tool with the given input.
        # For demonstration purposes, we'll just return a success message.
        return CommandResult(success=True, message="Tool used successfully.", data={"message_type": "tool"})
    except Exception as e:
        return CommandResult(success=False, message="Failed to use the specified tool.", error={"error": str(e)})
