import json

from src.system_logging.router import Router
from src.system_logging.on_time_registry import OnTimeRegistry
from src.system_logging.protocol import LogEntry
from src.utils.timestamp_util import get_formatted_timestamp


class Dispatcher:
    class DispatchError(RuntimeError):
        """Base class for dispatcher-related exceptions."""

        def __init__(self, message: str = ""):
            full_message = f"Dispatcher error: {message}" if message else "Dispatcher error"
            super().__init__(full_message)
            self.message = message

    @classmethod
    def dispatch(cls, message: str) -> None:
        """Dispatch the log entry to appropriate handlers registered in the OnTimeRegistry.

        Args:
            message (str): The log entry message to be dispatched.

        Returns:
            None
        """
        registry = OnTimeRegistry()

        log_entry = cls._convert_str_log_entry(message)

        try:
            handlers = registry.get_all_handlers()
        except OnTimeRegistry.RegistryError:
            # No handlers registered yet - this is normal during initialization
            return

        # Create router and determine LOG_TYPE based on content
        router = Router(log_entry, handlers)
        router.get_LOG_TYPE(only_for_custom=False)  # ← Determines and sets LOG_TYPE

        # Now route to appropriate handlers
        for handler in router.get_appropriate_handlers():
            handler.handle(log_entry)

    @staticmethod
    def _convert_str_log_entry(message: str) -> LogEntry:
        """
        Convert a string log entry into a LogEntry object.
        :param message: The log entry in string format.
        :return: LogEntry: The converted LogEntry object.

        the thing matter is to conver the string (JSON string) to the object but the
        structure of JSON is fixed :-

        data_type = LogType
        LogLevel = data[level]
        message = whole str
        timestamp = timestamp
        metadata = data[metadata]

        """
        from .protocol import LogLevel, LogCategory

        try:
            json_data = json.loads(message)
        except json.JSONDecodeError as e:
            raise Dispatcher.DispatchError(f"Invalid JSON format: {str(e)}")

        try:

            # Convert string values to enums
            log_type_str = json_data['LOG_TYPE']
            log_level_str = json_data['LEVEL']

            # Handle both enum values and enum objects
            if isinstance(log_type_str, str):
                log_type = LogCategory[log_type_str]
            else:
                log_type = log_type_str

            if isinstance(log_level_str, str):
                log_level = LogLevel[log_level_str]
            else:
                log_level = log_level_str

            log_entry = LogEntry(
                LOG_TYPE=log_type,
                LOG_LEVEL=log_level,
                MESSAGE=json_data['MESSAGE'],
                TIME_STAMP=json_data['TIME_STAMP'],
                METADATA=json_data.get('METADATA', {})
            )
        except (KeyError, ValueError) as e:
            ## fallback log_entry with minimal data
            log_entry = LogEntry(
                LOG_TYPE=LogCategory.OTHER,
                LOG_LEVEL=LogLevel.ERROR,
                MESSAGE=str(json_data.get('MESSAGE', message)),
                TIME_STAMP=get_formatted_timestamp(),
                METADATA=json_data.get('METADATA', {})
            )
        return log_entry
