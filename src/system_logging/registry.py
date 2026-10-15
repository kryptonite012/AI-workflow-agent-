from abc import ABC, abstractmethod

from .handlers.handler_base import Handler


class Registry(ABC):

    @abstractmethod
    def register(self, handler: Handler) -> None:
        """
        Register a logging component (e.g., handler, formatter) in the system.

        Args:
            handler : The Logging Handler which going to handle the log entry.

        Returns:
            None
        """
        raise NotImplementedError


    @abstractmethod
    def unregister(self, handler: Handler) -> None:
        """
        Unregister a logging component (e.g., handler, formatter) from the system.

        Args:
            handler : The Logging Handler which going to be unregistered.
        Returns:
            None
        """
        raise NotImplementedError




    class RegistryError(RuntimeError):
        """Base class for registry-related exceptions."""

        def __init__(self, handler: Handler | None = None):
            handler_name = handler.name if handler else None
            message = f"Handler '{handler_name}' registry error" if handler_name else "Handler registry error"
            super().__init__(message)
            self.handler_name = handler_name
