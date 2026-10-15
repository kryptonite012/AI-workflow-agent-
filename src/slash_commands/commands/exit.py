
from src.config import settings

from src.slash_commands.protocol import SlashCommand, CommandOption, CommandResult
from src.utils.listeners.exit_listener import ExitListener


def register_exit_command():
    """Function to register the /exit command."""
    from ..on_run_time_register import OnRunTimeRegistry

    exit_command = SlashCommand(
        command="exit",
        options=None,
        requirements=None,
        description="Exit the application.",
        handler=exit_handler
    )
    registry = OnRunTimeRegistry()
    try:
        registry.register(exit_command)
    except registry.CommandAlreadyRegisteredError:
        # Command is already registered; we can choose to log this or ignore it.
        pass

def exit_handler(command : SlashCommand, options : CommandOption) -> CommandResult:
    """Handler function to exit the application.

    :param command: The SlashCommand object for exit
    :param options: CommandOption for exit command flags, or None
    :return: CommandResult indicating success or failure of the operation.
    """

    try:
        # ✅ Use the standardized ticket system
        exit_listener : ExitListener = settings.listeners['exit']
        exit_listener.emit_exit_ticket(
            source_class=type(command),
            source_name="/exit_command"
        )

        # Don't set settings.exit_flag directly - let the ticket system handle it
        # settings.exit_flag = True  # ❌ Removed: Ticket system handles this

        return CommandResult(
            success=True,
            message="🎫 Exit ticket issued. Waiting for workflow completion...",
            data={"exit_ticket_issued": True}
        )

    except Exception as e:
        from src.ui.diagnostics.debug_helpers import debug_error
        debug_error(
            f"Error in exit_handler: {str(e)}",
            body="An error occurred while trying to emit exit ticket.",
            metadata={"exception": str(e)}
        )
        return CommandResult(success=False, message="Failed to issue exit ticket.", error={"error": str(e)})
