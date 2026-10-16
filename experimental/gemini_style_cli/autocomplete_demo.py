#!/usr/bin/env python3
"""
Standalone Auto-Complete Demo Script
Demonstrates real-time command suggestions like Gemini CLI
"""

import sys

from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

from src.config import settings

# For cross-platform keyboard input
try:
    import msvcrt  # Windows

    WINDOWS = True
except ImportError:
    import termios
    import tty

    WINDOWS = False

# Command registry - like Gemini CLI commands
COMMANDS = {
    "/help": "Show help information",
    "/search": "Search the web for information",
    "/translate": "Translate text to another language",
    "/rag": "Search in knowledge base",
    "/clear": "Clear the conversation",
    "/history": "Show conversation history",
    "/exit": "Exit the application",
    "/hello": "Say hello",
    "/health": "Check system health",
    "/home": "Go to home directory",
    "/host": "Show host information",
}


class AutoCompleteInput:
    def __init__(self):
        self.current_input = ""
        self.cursor_pos = 0
        self.suggestions = []
        self.selected_suggestion = 0

    def get_suggestions(self, text):
        """Get matching commands based on current input"""
        if not text.startswith("/"):
            return []

        matches = []
        for cmd in COMMANDS.keys():
            if cmd.startswith(text.lower()):
                matches.append(cmd)

        return sorted(matches)

    def get_best_suggestion(self):
        """Get the best matching suggestion"""
        if not self.suggestions:
            return ""
        return self.suggestions[0] if self.suggestions else ""

    def create_display(self):
        """Create the visual display with typed text + grayed suggestion"""
        display_text = Text()

        # Add the prompt
        display_text.append("You: ", style="bold cyan")

        # Add typed text
        display_text.append(self.current_input, style="bold white")

        # Add grayed suggestion
        best_suggestion = self.get_best_suggestion()
        if best_suggestion and best_suggestion.startswith(self.current_input):
            remaining = best_suggestion[len(self.current_input) :]
            display_text.append(remaining, style="dim white")

        # Add cursor
        display_text.append("█", style="bold white blink")

        return display_text

    def create_suggestions_panel(self):
        """Create panel showing all available suggestions"""
        if not self.suggestions:
            return Text("")

        suggestions_text = Text()
        suggestions_text.append("Available commands:\n", style="bold yellow")

        for i, cmd in enumerate(self.suggestions[:5]):  # Show max 5 suggestions
            style = "bold green" if i == self.selected_suggestion else "white"
            description = COMMANDS.get(cmd, "")
            suggestions_text.append(f"  {cmd}", style=style)
            suggestions_text.append(f" - {description}\n", style="dim white")

        if len(self.suggestions) > 5:
            suggestions_text.append(
                f"  ... and {len(self.suggestions) - 5} more", style="dim white"
            )

        return Panel(suggestions_text, title="Suggestions", border_style="blue")


def get_char():
    """Get a single character from stdin without pressing Enter"""
    if WINDOWS:
        return msvcrt.getch().decode("utf-8", errors="ignore")
    else:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            char = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return char


def main():
    console = settings.console
    console.print(
        Panel.fit(
            "[bold magenta]Auto-Complete Demo[/bold magenta]\n"
            "[cyan]Type commands starting with '/' to see suggestions[/cyan]\n"
            "[yellow]Controls:[/yellow]\n"
            "  • Type: See real-time suggestions\n"
            "  • Tab: Complete suggestion\n"
            "  • Enter: Execute command\n"
            "  • Backspace: Delete character\n"
            "  • Ctrl+C: Exit\n",
            title="Welcome",
            border_style="green",
        )
    )

    autocomplete = AutoCompleteInput()

    try:
        while True:
            # Create layout
            layout = Layout()
            layout.split_column(
                Layout(name="input", size=3),
                Layout(name="suggestions", size=10),
                Layout(name="output", size=5),
            )

            # Update suggestions based on current input
            autocomplete.suggestions = autocomplete.get_suggestions(
                autocomplete.current_input
            )

            # Create display components
            input_display = Panel(
                autocomplete.create_display(), title="Input", border_style="cyan"
            )
            suggestions_display = autocomplete.create_suggestions_panel()

            # Status info
            status_text = Text()
            if autocomplete.current_input:
                status_text.append(
                    f"Input: '{autocomplete.current_input}' | ", style="white"
                )
                status_text.append(
                    f"Suggestions: {len(autocomplete.suggestions)}", style="green"
                )
            else:
                status_text.append(
                    "Start typing a command with '/' to see suggestions...",
                    style="dim white",
                )

            status_panel = Panel(status_text, title="Status", border_style="yellow")

            # Update layout
            layout["input"].update(input_display)
            layout["suggestions"].update(suggestions_display)
            layout["output"].update(status_panel)

            # Display everything
            console.clear()
            console.print(layout)
            console.print("\n[dim]Press Ctrl+C to exit[/dim]")

            # Get user input
            try:
                char = get_char()

                # Handle special keys
                if ord(char) == 3:  # Ctrl+C
                    break
                elif ord(char) == 13:  # Enter
                    if autocomplete.current_input:
                        console.print(
                            f"\n[green]Executed:[/green] {autocomplete.current_input}"
                        )
                        if autocomplete.current_input in COMMANDS:
                            console.print(
                                f"[blue]Description:[/blue] {COMMANDS[autocomplete.current_input]}"
                            )
                        console.print("\n[yellow]Press any key to continue...[/yellow]")
                        get_char()
                        autocomplete.current_input = ""
                elif ord(char) == 9:  # Tab
                    best_suggestion = autocomplete.get_best_suggestion()
                    if best_suggestion:
                        autocomplete.current_input = best_suggestion
                elif ord(char) == 8 or ord(char) == 127:  # Backspace
                    if autocomplete.current_input:
                        autocomplete.current_input = autocomplete.current_input[:-1]
                elif ord(char) >= 32:  # Printable characters
                    autocomplete.current_input += char

            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                break

    except KeyboardInterrupt:
        pass

    console.print("\n[green]Thanks for trying the auto-complete demo![/green]")


if __name__ == "__main__":
    main()
