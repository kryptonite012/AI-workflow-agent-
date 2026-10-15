"""
this is routing slash command to move make user chat with llm
"""
from src.slash_commands.protocol import SlashCommand, CommandResult, CommandOption
from src.slash_commands.on_run_time_register import OnRunTimeRegistry

def register_chat_llm_command():
    chat_llm_command = SlashCommand(
        command="llm",
        options=None,
        requirements=None,
        description="Send a message to the LLM and get a response.",
        handler=chat_llm_handler
    )
    registry = OnRunTimeRegistry()
    try:
        registry.register(chat_llm_command)
    except registry.CommandAlreadyRegisteredError:
        # Command is already registered; we can choose to log this or ignore it.
        pass

def chat_llm_handler(command: SlashCommand, options: CommandOption | None) -> CommandResult:
    """Handler function to route message to LLM chat interface.

    :param command: The SlashCommand object for llm
    :param options: CommandOption for llm command flags, or None
    :return: CommandResult indicating success or failure of the operation.
    """
    try:
        # Here you would implement the actual logic to send the message to the LLM and get a response.
        # For demonstration purposes, we'll just return a success message.
        return CommandResult(success=True, message="Message sent to LLM successfully.", data={"message_type": "llm"})
    except Exception as e:
        return CommandResult(success=False, message="Failed to send message to LLM.", error={"error": str(e)})