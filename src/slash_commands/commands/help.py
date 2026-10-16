from ..protocol import SlashCommand, CommandResult, CommandOption
from ..on_run_time_register import OnRunTimeRegistry

def register_help_command() -> None:
    """Function to register the /help command in the OnRunTimeRegistry."""
    help_command = SlashCommand(
        command="help",
        options=[CommandOption(name="command", description="for displaying help messages for commands and features")],  # Help command can take optional arguments for specific command help
        requirements=None,
        description="Show available commands and their usage.",
        handler=help_handler
    )
    registry = OnRunTimeRegistry()
    try:
        registry.register(help_command)
    except registry.CommandAlreadyRegisteredError:
        # Command is already registered; we can choose to log this or ignore it.
        pass


def help_handler(command: SlashCommand, options: CommandOption | None) -> CommandResult:
    """Handler function to display help information for available commands.
    
    :param command: The SlashCommand object for help
    :param options: CommandOption for specific command help, or None for general help
    :return: CommandResult with help information
    """
    registry = OnRunTimeRegistry()
    try:
        if options and options.value:
            # that means user asked for specific command help e.g. ❌ /help --command clear info ✅ /help --command clear
            if options.name == "command":
                if len(options.value) > 1:
                    CommandResult(success=False, message="Please provide only one command name for specific help.", error={"error": "Too many command names"})
                single_com_info = get_specific_command_help(options.value[0])
                # because the options are allowed only one ❌ /help --command clear info ✅ /help --command clear
                if isinstance(single_com_info, Exception):
                    return CommandResult(success=False, message="Failed to retrieve specific command help.", error={"error": str(single_com_info)})
                elif single_com_info is None:
                    return CommandResult(success=False, message=f"No help found for command '{options.value[0]}'.", error={"error": "Command not found"})
                else:
                    return CommandResult(success=True, message=single_com_info)
            else:
                return CommandResult(success=False, message=f"Invalid option for help command. Use --command <command_name>. provided {options.name}", error={"error": "Invalid option"})
        # General help: list all commands
        help_message = "Available Commands:\n"
        for cmd in registry:
            help_message += get_specific_command_help(cmd.command)
        return CommandResult(success=True, message=help_message)
    except registry.CommandNotFoundError as e:
        return CommandResult(success=False, message="Failed to retrieve help information.", error={"error": str(e)})


def get_specific_command_help(command_name: str) -> str | None | Exception:
    """Retrieve help information for specific commands.

    :param command_name: str of command name to get help for
    :return: CommandResult with specific command help information
    """
    registry = OnRunTimeRegistry()
    try:
        specific_command = registry.get(command_name)
        help_message = f"Command: /{specific_command.command}\nDescription: {specific_command.description or 'No description available.'}\n"
        if specific_command.options:
            help_message += "Options:\n"
            for option in specific_command.options:
                help_message += f"  --{option.name}: {option.description or 'No description available.'} (Required: {option.required})\n"
        else:
            help_message += "No options available for this command.\n"
        return help_message
    except registry.CommandNotFoundError:
        return None
    except Exception as e:
        return e