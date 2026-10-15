#!/usr/bin/env python3
"""
Simple Auto-Complete Demo using prompt_toolkit
This shows exactly how Gemini CLI-style suggestions work
"""

from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.shortcuts import CompleteStyle
from rich.panel import Panel
from rich.text import Text

from src.config import settings

# Command registry - exactly like Gemini CLI
COMMANDS = {
    "/help": "Show help information",
    "/search": "Search the web for information",
    "/translate": "Translate text to another language",
    "/rag": "Search in knowledge base",
    "/clear": "Clear the conversation",
    "/history": "Show conversation history",
    "/exit": "Exit the application",
    "/hello": "Say hello to the user",
    "/health": "Check system health status",
    "/home": "Navigate to home directory",
    "/host": "Show host information",
}


class SmartCompleter(Completer):
    """Custom completer that shows descriptions and handles smart matching"""

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        # Only suggest commands that start with '/'
        if text.startswith("/"):
            for command, description in COMMANDS.items():
                if command.startswith(text.lower()):
                    # Calculate how much to complete
                    completion_text = command[len(text) :]

                    yield Completion(
                        completion_text,
                        display=f"{command} - {description}",
                        start_position=0,
                    )


def print_banner():
    """Print welcome banner"""
    console = settings.console
    banner_text = Text()
    banner_text.append("🚀 Auto-Complete Demo\n", style="bold magenta")
    banner_text.append(
        "Type commands starting with '/' to see magic happen!\n\n", style="cyan"
    )
    banner_text.append("Available commands:\n", style="yellow")

    for cmd, desc in list(COMMANDS.items())[:5]:
        banner_text.append(f"  {cmd}", style="bold green")
        banner_text.append(f" - {desc}\n", style="white")

    banner_text.append(
        f"  ... and {len(COMMANDS) - 5} more commands\n\n", style="dim white"
    )
    banner_text.append("✨ Features:\n", style="yellow")
    banner_text.append("  • Real-time suggestions as you type\n", style="white")
    banner_text.append("  • Tab to complete\n", style="white")
    banner_text.append("  • Fuzzy matching\n", style="white")
    banner_text.append("  • Command descriptions\n", style="white")

    console.print(Panel(banner_text, title="Welcome", border_style="blue"))


def execute_command(command_input):
    """Execute the entered command"""
    console = settings.console
    parts = command_input.strip().split()
    if not parts:
        return

    command = parts[0]
    args = parts[1:] if len(parts) > 1 else []

    if command in COMMANDS:
        console.print(f"[green]✅ Executing:[/green] [bold]{command}[/bold]")
        console.print(f"[blue]Description:[/blue] {COMMANDS[command]}")
        if args:
            console.print(f"[yellow]Arguments:[/yellow] {' '.join(args)}")

        # Simulate command execution
        if command == "/exit":
            return False
        elif command == "/help":
            show_help()
        elif command == "/clear":
            console.clear()
        else:
            console.print(f"[dim]Command '{command}' executed successfully![/dim]")
    else:
        console.print(f"[red]❌ Unknown command:[/red] {command}")
        console.print("[yellow]💡 Tip:[/yellow] Type '/' to see available commands")

    return True


def show_help():
    """Show help information"""
    console = settings.console
    help_text = Text()
    help_text.append("📚 Available Commands:\n\n", style="bold yellow")

    for cmd, desc in COMMANDS.items():
        help_text.append(f"  {cmd}", style="bold green")
        help_text.append(f" - {desc}\n", style="white")

    console.print(Panel(help_text, title="Help", border_style="green"))


def main():
    """Main demo loop"""
    console = settings.console
    console.clear()
    print_banner()

    # Create the completer
    completer = SmartCompleter()

    console.print("\n[bold cyan]🎯 Try typing these examples:[/bold cyan]")
    console.print("  • Type [bold]'/h'[/bold] and see suggestions")
    console.print("  • Type [bold]'/se'[/bold] and press Tab")
    console.print("  • Type [bold]'/help'[/bold] and press Enter")
    console.print("  • Type [bold]'/exit'[/bold] to quit\n")

    while True:
        try:
            # This is where the magic happens!
            user_input = prompt(
                "🤖 You: ",
                completer=completer,
                complete_style=CompleteStyle.READLINE_LIKE,  # Shows grayed suggestions
                mouse_support=True,
                # Enable completion menu
                complete_while_typing=True,
            )

            if user_input.strip():
                if not execute_command(user_input):
                    break

            console.print()  # Add spacing

        except KeyboardInterrupt:
            console.print("\n[yellow]👋 Goodbye![/yellow]")
            break
        except EOFError:
            break


if __name__ == "__main__":
    # Install required packages
    try:
        import prompt_toolkit
    except ImportError:
        console.print("[red]❌ Missing dependency![/red]")
        console.print("Please install: [bold]pip install prompt-toolkit[/bold]")
        exit(1)

    main()
