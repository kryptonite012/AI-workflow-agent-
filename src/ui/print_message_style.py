from src.utils.sound import beep
from rich.align import Align
from rich.panel import Panel

from src.config import settings


def print_message(msg: str, sender="user"):
    console = settings.console
    if sender == "user":
        icon = "👤"
        style = "bold cyan"
        label = "[USER]"
    elif sender == "ai":
        icon = "🤖"
        style = "bold green"
        label = "[AI]"
    elif sender == "tool":
        icon = "🛠️"
        style = "bold yellow"
        label = "[TOOL]"
    else:
        icon = ""
        style = ""
        label = ""

    # Fix: Handle newlines properly by using Rich's built-in newline support
    # Instead of Text(), use a simple string which Rich handles newlines correctly
    formatted_message = f"{icon} {label} {msg.strip()}"

    panel = Panel(
        Align.left(formatted_message),
        border_style=style,
        padding=(1, 2),
    )
    console.print(panel)
    if settings.ENABLE_SOUND_NOTIFICATIONS:
        beep(7200, 200)  # Play a sound for new message
