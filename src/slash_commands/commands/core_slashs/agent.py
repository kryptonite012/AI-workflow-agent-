from ...protocol import SlashCommand, CommandOption, CommandResult
from ...on_run_time_register import OnRunTimeRegistry


def register_agent_command():
    """Function to register the /agent command in the OnRunTimeRegistry."""
    commands_options = [
        CommandOption(name="low", description="For simple tasks like telling a joke, fetching a quote, etc.", required=False),
        CommandOption(name="medium", description="For moderately complex tasks like summarizing text, basic data analysis, etc.", required=False),
        CommandOption(name="high", description="For complex tasks like market analysis, strategic planning, etc.", required=False),
    ]
    agent_command = SlashCommand(
        command="agent",
        options=commands_options,  # Agent command can take optional arguments for complexity level
        requirements=None,
        description="Invoke a specific agent to perform a task based on complexity level.",
        handler=agent_handler
    )
    registry = OnRunTimeRegistry()
    try:
        registry.register(agent_command)
    except registry.CommandAlreadyRegisteredError:
        # Command is already registered; we can choose to log this or ignore it.
        pass
    pass

def agent_handler(command: SlashCommand | None, options: CommandOption | None) -> CommandResult:
    """Handler function to invoke a specific agent to perform a task.
    e.g.
        /agent --low tell me a joke
        /agent --medium summarize the following text
        /agent --high analyze the market trends for next week
    0. low - simple tasks like telling a joke, fetching a quote, etc.
    1. medium - moderately complex tasks like summarizing text, basic data analysis, etc
    2. high - complex tasks like market analysis, strategic planning, etc.
    todo this our agent is not implemented yet, this is just a placeholder for future development
    todo where the agent response could vary based on the complexity level (that could be required diff prompts for each to consume more requests)
    todo for now we are just routing to the agent node based on the option provided
    :param command: The SlashCommand object for agent
    :param options: CommandOption for agent command flags, or None
    :return: CommandResult indicating success or failure of the operation.
    """
    try:
        # Here you would implement the actual logic to invoke the specified agent with given options.
        # For demonstration purposes, we'll just return a success message.
        # todo in future we would use the handlers below but for now just route to agent node

        return CommandResult(success=True, message="Agent invoked successfully.", data={"message_type": "agent"})
    except Exception as e:
        return CommandResult(success=False, message="Failed to invoke agent.", error={"error": str(e)})


def _handle_low_option(options: CommandOption) -> str | None | Exception:
    """Handle low complexity tasks."""
    # Implement logic for low complexity tasks
    return "Handled low complexity task."

def _handle_medium_option(options: CommandOption) -> str | None | Exception:
    """Handle medium complexity tasks."""
    # Implement logic for medium complexity tasks
    return "Handled medium complexity task."

def _handle_high_option(options: CommandOption) -> str | None | Exception:
    """Handle high complexity tasks."""
    # Implement logic for high complexity tasks
    return "Handled high complexity task."