from ..protocol import SlashCommand, CommandResult, CommandOption
from ..on_run_time_register import OnRunTimeRegistry
from ...models.state import StateAccessor
from ...tools.lggraph_tools.tool_response_manager import ToolResponseManager


def register_clear_command() -> None:
    """Function to register the /clear command in the OnRunTimeRegistry."""
    clear_command = SlashCommand(
        command="clear",
        options=None, # clear whole chat history no options needed
        requirements=None,
        description="Clear the chat history or context.",
        handler=clear_handler
    )
    registry = OnRunTimeRegistry()
    try:
        registry.register(clear_command)
    except registry.CommandAlreadyRegisteredError:
        # Command is already registered; we can choose to log this or ignore it.
        pass

def clear_handler(command: SlashCommand, options: CommandOption | None) -> CommandResult:
    """Handler function to clear the chat history, context and screen .
    e.g. /clear --force true
    :param command: The SlashCommand object for clear
    :param options: CommandOption for clear command flags, or None
    :return: CommandResult indicating success or failure of the operation.
    """
    try:
        import os
        # Here you would implement the actual logic to clear the chat history or context.
        # For demonstration purposes, we'll just return a success message.

        # Check for --force option
        force_clear = False
        if options and options.value:
            force_clear = "--force" in options.value or "force" in options.value

        # clear chat means clearing the context history screen or any stored messages (but could log it somewhere else if needed)
        ToolResponseManager().clear_response()
        StateAccessor().clear_state()
        os.system('cls' if os.name == 'nt' else 'clear')  # Clear terminal screen (optional)
        return CommandResult(success=True, message="Chat history cleared successfully.")
    except Exception as e:
        return CommandResult(success=False, message="Failed to clear chat history.", error={"error": str(e)})