
from .protocol import SlashCommand
from .registry import Registry


class OnRunTimeRegistry(Registry):
    """on the run time when the application got started this is the
    actual registry provided by the application on default ...
    """

    _registered_commands: list[SlashCommand]
    instance = None
    _lock = None

    def register(self, slash_command: SlashCommand) -> None:
        """Register a handler for the given command metadata.
        :raise CommandAlreadyRegisteredError: if the command is already registered
        """
        if slash_command in self._registered_commands:
            raise Registry.CommandAlreadyRegisteredError(slash_command)
        elif any(cmd for cmd in self._registered_commands if cmd.command == slash_command.command):
            raise Registry.CommandAlreadyRegisteredError(slash_command)
        self._registered_commands.append(slash_command)

    def unregister(self, slash_command: SlashCommand) -> None:
        """Remove a command handler by command name.
        :raise CommandNotFoundError: if not found. If the command is not registered
        """
        found_slash_command = self.get(slash_command.command)
        self._registered_commands.remove(found_slash_command)

    def get(self, command: str) -> SlashCommand:
        """Return SlashCommand for the given command name.
        :raise CommandNotFoundError: if not found. If the command is not registered
        """
        slash_command = next((cmd for cmd in self._registered_commands if cmd.command == command), None)
        if not slash_command:
            raise Registry.CommandNotFoundError()
        return slash_command

    def __len__(self):
        """Return the number of registered commands."""
        return len(self._registered_commands)

    def __contains__(self, slash_command: SlashCommand) -> bool:
        """Return True if the command or command name is registered.
        :arg slash_command: the slash command obj to check the name from
        """
        command_name = slash_command.command
        return any(cmd for cmd in self._registered_commands if cmd.command == command_name) or slash_command in self._registered_commands

    def __delitem__(self, key):
        # allow either str (command name) or SlashCommand instance
        with self._lock:
            if isinstance(key, str):
                slash_command = self.get(key)
                self._registered_commands.remove(slash_command)
            elif isinstance(key, SlashCommand):
                if key in self._registered_commands:
                    self._registered_commands.remove(key)
                else:
                    raise Registry.CommandNotFoundError()
            else:
                raise TypeError("Key must be a command name (str) or SlashCommand instance.")

    def __iter__(self):
        return iter(self._registered_commands)

    def __new__(cls):
        """Thread-safe singleton pattern to ensure only one instance of OnRunTimeRegistry exists.

        :return: The single instance of OnRunTimeRegistry.
        """
        import threading
        if not hasattr(cls, "_lock") or cls._lock is None:
            cls._lock = threading.Lock()

        with cls._lock:
            if cls.instance is None:
                cls.instance = super(OnRunTimeRegistry, cls).__new__(cls)
                cls.instance._registered_commands = []
        return cls.instance
