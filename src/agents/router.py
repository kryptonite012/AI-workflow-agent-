from src.config import settings
from src.models.state import StateAccessor


def route_message(state):
    """Determines the next node in the workflow based on the classified message type.
    """
    console = settings.console
    state_accessor = StateAccessor()
    console.print("\t\t[bold][green]----Node is router[/bold][/green]")
    # 🔄 Sync StateAccessor with current LangGraph state
    state_accessor.sync_with_langgraph(state)
    message_type = state.get("message_type", "llm")
    return {"message_type": message_type}
