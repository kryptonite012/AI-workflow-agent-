import threading
from .handlers.handler_base import Handler
from .registry import Registry


class OnTimeRegistry(Registry):
    """Registry for on-time logging components (Singleton)."""
    _instance = None
    _lock = threading.Lock()
    _handlers: dict[str, Handler] = {}

    def __new__(cls):
        """Ensure only one instance of OnTimeRegistry exists."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, handler) -> None:
        """
        Register a logging handler in the on-time registry.

        Args:
            handler : The Logging Handler which going to handle the log entry.

        Returns:
            None
        """
        if handler.name in self._handlers:
            raise self.RegistryError(handler)
        self._handlers[handler.name] = handler

    def unregister(self, handler) -> None:
        """
        Unregister a logging handler from the on-time registry.

        Args:
            handler : The Logging Handler which going to be unregistered.
        Returns:
            None
        """
        if handler.name not in self._handlers:
            raise self.RegistryError(handler)
        del self._handlers[handler.name]


    def get(self, handler_name: str) -> object:
        """
        Retrieve a logging handler by name from the on-time registry.

        Args:
            handler_name (str): The name of the handler to retrieve.

        Returns:
            object: The logging handler associated with the given name.

        Raises:
            RegistryError: If the handler is not found in the registry.
        """
        if handler_name not in self._handlers:
            raise self.RegistryError()
        return self._handlers[handler_name]


    def __len__(self):
        """Return the number of registered handlers."""
        return len(self._handlers)


    def __contains__(self, handler) -> bool:
        """Return True if the handler is registered.
        :arg handler: the handler obj to check the name from
        """
        return handler.name in self._handlers


    def __delitem__(self, key):
        # allow either str (handler name) or Handler instance
        if isinstance(key, str):
            if key not in self._handlers:
                raise self.RegistryError()
            del self._handlers[key]
        else:
            if key.name not in self._handlers:
                raise self.RegistryError()
            del self._handlers[key.name]



    def get_all_handlers(self) -> list[Handler]:
        """Return a list of all registered handlers."""
        if not self._handlers or len(self._handlers) == 0:
            raise self.RegistryError()

        return list(self._handlers.values())

