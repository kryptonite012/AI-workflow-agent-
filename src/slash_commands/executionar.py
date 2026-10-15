from .protocol import SlashCommand, CommandOption, CommandResult
from .on_run_time_register import OnRunTimeRegistry


class ExecutionAr:
    """Class to execute registered slash commands."""

    def __init__(self):
        self.registry = OnRunTimeRegistry()

    def execute(self, slash_com:SlashCommand) -> CommandResult:
        """Execute a registered slash command.
        :param slash_com: SlashCommand instance containing the command name and options. fetched from parser
        :type slash_com: SlashCommand
        :returns:CommandResult with execution outcome; on error returns success=False and error details.
        :rtype: CommandResult
        """
        try:
            registered_command_details = self.registry.get(slash_com.command)
            # todo apply any pre-processing middleware or validation on options if needed
            return registered_command_details.handler(slash_com, slash_com.options[0] if slash_com.options else None)
        except self.registry.CommandNotFoundError:
            return CommandResult(success=False, message=f"Command '{slash_com.command}' not found.", error={"error": "Command not found"})
        except Exception as e:
            return CommandResult(success=False, message="Failed to execute command.", error={"error": str(e)})