#!/usr/bin/env python3
"""
Inline Suggestion Demo - Shows exactly how Gemini CLI suggestions work
This replicates the behavior where you type '/h' and see 'elp' grayed out
"""

import sys

from rich.panel import Panel
from rich.text import Text

from src.config import settings

# Cross-platform keyboard input
try:
    import msvcrt

    WINDOWS = True
except ImportError:
    import termios, tty

    WINDOWS = False

# Commands like Gemini CLI
COMMANDS = {
    "/help": "Show help information",
    "/search": "Search the web",
    "/translate": "Translate text",
    "/rag": "Search knowledge base",
    "/clear": "Clear conversation",
    "/history": "Show history",
    "/exit": "Exit application",
    "/hello": "Say hello",
    "/health": "System health",
    "/home": "Go home",
}


def get_char():
    """Get single character input"""
    if WINDOWS:
        return msvcrt.getch().decode("utf-8", errors="ignore")
    else:
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            char = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        return char


def get_best_match(input_text):
    """Get the best matching command"""
    if not input_text.startswith("/"):
        return None

    matches = [cmd for cmd in COMMANDS.keys() if cmd.startswith(input_text.lower())]
    return matches[0] if matches else None


def create_input_display(current_input, cursor_visible=True):
    """Create the input display with inline suggestions"""
    display = Text()

    # Prompt
    display.append("🤖 You: ", style="bold cyan")

    # Current typed text
    display.append(current_input, style="bold white")

    # Inline suggestion (grayed out)
    best_match = get_best_match(current_input)
    if best_match and len(current_input) > 0:
        suggestion_part = best_match[len(current_input) :]
        display.append(suggestion_part, style="dim white")

    # Cursor
    if cursor_visible:
        display.append("█", style="bold white")

    return display


def create_suggestions_list(current_input):
    """Create list of all matching suggestions"""
    if not current_input.startswith("/"):
        return Text("Type '/' to see commands...", style="dim yellow")

    matches = [cmd for cmd in COMMANDS.keys() if cmd.startswith(current_input.lower())]

    if not matches:
        return Text("No matching commands", style="dim red")

    suggestions = Text()
    suggestions.append("💡 Suggestions:\n", style="bold yellow")

    for i, cmd in enumerate(matches[:6]):  # Show max 6
        if i == 0:  # Highlight best match
            suggestions.append(f"  ▶ {cmd}", style="bold green")
        else:
            suggestions.append(f"    {cmd}", style="white")

        desc = COMMANDS.get(cmd, "")
        suggestions.append(f" - {desc}\n", style="dim white")

    if len(matches) > 6:
        suggestions.append(f"    ... and {len(matches) - 6} more\n", style="dim white")

    return suggestions


def main():
    """Main demo"""
    console = settings.console
    console.clear()

    # Welcome message
    welcome = Text()
    welcome.append("🚀 Inline Suggestion Demo\n", style="bold magenta")
    welcome.append("Experience Gemini CLI-style auto-complete!\n\n", style="cyan")
    welcome.append("✨ What you'll see:\n", style="yellow")
    welcome.append("  • Type '/h' → see 'elp' grayed out\n", style="white")
    welcome.append("  • Press Tab → complete the suggestion\n", style="white")
    welcome.append("  • Press Enter → execute command\n", style="white")
    welcome.append("  • Backspace → delete characters\n\n", style="white")
    welcome.append("🎯 Try typing: /h, /se, /tr, /ex\n", style="bold green")

    console.print(Panel(welcome, title="Welcome", border_style="blue"))
    console.print()

    current_input = ""
    cursor_blink = True

    try:
        while True:
            # Create display
            input_display = create_input_display(current_input, cursor_blink)
            suggestions_display = create_suggestions_list(current_input)

            # Show current state
            console.clear()
            console.print(Panel(welcome, title="Welcome", border_style="blue"))
            console.print()
            console.print(Panel(input_display, title="Input", border_style="cyan"))
            console.print()
            console.print(
                Panel(
                    suggestions_display,
                    title="Available Commands",
                    border_style="green",
                )
            )

            # Instructions
            instructions = Text()
            instructions.append("Controls: ", style="bold yellow")
            instructions.append("Tab", style="bold green")
            instructions.append("=complete, ", style="white")
            instructions.append("Enter", style="bold green")
            instructions.append("=execute, ", style="white")
            instructions.append("Backspace", style="bold green")
            instructions.append("=delete, ", style="white")
            instructions.append("Ctrl+C", style="bold red")
            instructions.append("=exit", style="white")

            console.print(Panel(instructions, border_style="yellow"))

            # Get input
            char = get_char()

            if ord(char) == 3:  # Ctrl+C
                break
            elif ord(char) == 13:  # Enter
                if current_input.strip():
                    console.clear()
                    if current_input in COMMANDS:
                        result = Text()
                        result.append("✅ Command Executed!\n", style="bold green")
                        result.append(f"Command: {current_input}\n", style="bold white")
                        result.append(
                            f"Description: {COMMANDS[current_input]}\n", style="cyan"
                        )
                        console.print(
                            Panel(
                                result, title="Execution Result", border_style="green"
                            )
                        )

                        if current_input == "/exit":
                            break
                    else:
                        error = Text()
                        error.append("❌ Unknown Command!\n", style="bold red")
                        error.append(f"You typed: {current_input}\n", style="white")
                        error.append(
                            "Try typing '/' to see available commands", style="yellow"
                        )
                        console.print(Panel(error, title="Error", border_style="red"))

                    console.print("\n[dim]Press any key to continue...[/dim]")
                    get_char()
                    current_input = ""

            elif ord(char) == 9:  # Tab - Complete suggestion
                best_match = get_best_match(current_input)
                if best_match:
                    current_input = best_match

            elif ord(char) == 8 or ord(char) == 127:  # Backspace
                if current_input:
                    current_input = current_input[:-1]

            elif ord(char) >= 32 and ord(char) < 127:  # Printable characters
                current_input += char

            # Toggle cursor blink effect
            cursor_blink = not cursor_blink

    except KeyboardInterrupt:
        pass

    console.clear()
    goodbye = Text()
    goodbye.append("👋 Thanks for trying the demo!\n", style="bold green")
    goodbye.append("This is exactly how Gemini CLI suggestions work.", style="cyan")
    console.print(Panel(goodbye, title="Goodbye", border_style="green"))


if __name__ == "__main__":
    main()
