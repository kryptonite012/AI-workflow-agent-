"""
slash_commands.registry
=======================

Abstract registry protocol for managing slash command handlers.

This module defines the abstract base class `Registry` which specifies the
minimal protocol required to register, unregister, retrieve and manage
`SlashCommand` handlers. It also defines the registry-specific exceptions
used by implementations:

- `Registry.CommandNotFoundError`:
  raised when a requested command is not present in the registry.
- `Registry.CommandAlreadyRegisteredError`:
  raised when attempting to register a command that already exists.
- `Registry.CommandExecutionError`:
  raised when a handler fails while executing a command; it can wrap the
  original exception.

Key abstract methods expected from concrete implementations:
- `register(command: SlashCommand) -> None`
- `unregister(command: SlashCommand) -> None`
- `get(command: SlashCommand) -> SlashCommand`
- `__len__()`, `__contains__(command: SlashCommand) -> bool`, `__delitem__(key)`

Designed to be IDE-friendly for PyCharm with clear signatures and exceptions,
so implementations and callers can rely on static analysis and quick navigation.
"""

from abc import ABC, abstractmethod
from .protocol import SlashCommand


class Registry(ABC):
    """Abstract base class defining the command registry protocol.

        Concrete implementations must provide methods to register, unregister,
        lookup and manage `SlashCommand` handlers. This docstring lists the
        required abstract methods and the registry-specific exceptions to aid
        PyCharm inspections and static analysis.

        Required methods (signatures shown for clarity):
            register(command: SlashCommand) -> None
            unregister(command: SlashCommand) -> None
            get(command: SlashCommand) -> SlashCommand
            __len__() -> int
            __contains__(command: SlashCommand) -> bool
            __delitem__(key) -> None

        Exceptions:
            - CommandNotFoundError: raised when a requested command is not present.
            - CommandAlreadyRegisteredError: raised when registering an existing command.
            - CommandExecutionError: raised/wraps when a handler fails during execution.

        Notes:
            - Implementations should accept either a `SlashCommand` instance or a
              command name where appropriate and normalize inputs consistently.
            - Preserve type hints on overrides so PyCharm and linters can verify usage.
            - If the registry is accessed concurrently, implementations should ensure
              thread-safety.
        """

    @abstractmethod
    def register(self, command: SlashCommand) -> None:
        """Register a handler for the given command metadata."""
        raise NotImplementedError

    @abstractmethod
    def unregister(self, command: SlashCommand) -> None:
        """Remove a command handler by command name.
        :raise KeyError: if not found. If the command is not registered
        """
        raise NotImplementedError

    @abstractmethod
    def get(self, command: SlashCommand) -> SlashCommand:
        """Return SlashCommand for the given command name.
        :raise CommandNotFoundError: if not found. If the command is not registered
        """
        raise NotImplementedError

    def __len__(self):
        """Return the number of registered commands."""
        raise NotImplementedError

    def __contains__(self, command: SlashCommand) -> bool:
        """Return True if the command is registered.
        :arg command: the command name to check for
        """
        raise NotImplementedError

    def __delitem__(self, key):
        """Remove a command handler by command name or SlashCommand instance.
        :raise CommandNotFoundError: if not found. If the command is not registered
        """
        raise NotImplementedError

    class CommandNotFoundError(KeyError):
        """Raised when a command is not found in the registry."""

        def __init__(self, slash_command: SlashCommand | None = None):
            command_name = slash_command.command if slash_command else None
            message = f"Slash command '{command_name}' not registered" if command_name else "Slash command not registered"
            super().__init__(message)
            self.command_name = command_name

    class CommandAlreadyRegisteredError(RuntimeError):
        """Raised when a command is already registered in the registry."""

        def __init__(self, slash_command: SlashCommand | None = None):
            command_name = slash_command.command if slash_command else None
            message = f"Slash command '{command_name}' already registered" if command_name else "Slash command already registered"
            super().__init__(message)
            self.command_name = command_name

    class CommandExecutionError(RuntimeError):
        """Raised when a command handler fails to execute the command could return the actual error which it encountered."""

        def __init__(self, slash_command: SlashCommand | None = None, original_exception: Exception | None = None):
            command_name = slash_command.command if slash_command else None
            message = f"Execution of slash command '{command_name}' failed" if command_name else "Execution of slash command failed"
            if original_exception:
                message += f" with : {original_exception!s}"
            super().__init__(message)
            self.command_name = command_name
            self.original_exception = original_exception
