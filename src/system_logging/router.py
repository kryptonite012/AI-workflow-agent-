from .handlers.handler_base import Handler
from .protocol import LogCategory, LogEntry


class Router:
    """
    Routes log entries to appropriate handlers based on their LOG_TYPE.

    Features:
    1. Dynamically determines LOG_TYPE by keyword matching in heading
    2. Supports custom keyword→category mappings via custom_routes
    3. Extensible - add new routing rules without changing code
    4. Uses metadata heading (from adapter) for accurate categorization
    """

    # Default keyword mappings: keyword → LogCategory
    # These can be customized per instance
    DEFAULT_KEYWORD_MAP = {
        "MCP": LogCategory.MCP_SERVER,
        "API": LogCategory.API_CALL,
        "OPENAI": LogCategory.API_CALL,
        "OLLAMA": LogCategory.API_CALL,
        "TOOL": LogCategory.TOOL_EXECUTION,
        "AGENT": LogCategory.AGENT_WORKFLOW,
        "WORKFLOW": LogCategory.AGENT_WORKFLOW,
        "ERROR": LogCategory.ERROR_TRACEBACK,
        "FAILED": LogCategory.ERROR_TRACEBACK,
        "TRACEBACK": LogCategory.ERROR_TRACEBACK,
    }

    _custom_routes: dict = {}

    def __init__(self, log_entry:LogEntry, handlers:list[Handler]):
        self.log_entry = log_entry
        self.handlers = handlers



    @property
    def custom_routes(self) -> dict:
        return self._custom_routes


    @custom_routes.setter
    def custom_routes(self, routes: dict) -> None:
        """
        Set custom routes for log entry categorization.
        :param routes : dict: A dictionary mapping keywords to LogCategory.
        :return:
        """
        self._custom_routes = routes


    def add_handler(self, handler: Handler) -> None:
        """
        Add a new handler to the router's handler list.
        :param handler: The handler to be added.
        :return: None
        """
        self.handlers.append(handler)




    def get_LOG_TYPE(self, only_for_custom: bool = False) -> LogEntry:
        """
        Dynamically determine and assign LOG_TYPE for the current log entry.

        Routing Strategy:
        1. Extract heading from METADATA (adapter stores it there)
        2. Match keywords in heading against keyword→category mappings
        3. Use custom_routes if only_for_custom=True, else use both default + custom
        4. First match wins (priority order matters)
        5. Fallback to OTHER if no match found

        :param only_for_custom: If True, only use custom_routes. If False, use default + custom.
        :type only_for_custom: bool
        :return: The LogEntry instance with LOG_TYPE set to the determined category.
        :rtype: LogEntry
        """
        # Extract heading from metadata (adapter preserved it!)
        heading = ""
        if self.log_entry.METADATA and isinstance(self.log_entry.METADATA, dict):
            heading = self.log_entry.METADATA.get("heading", "").upper()

        # If no heading in metadata, try to parse from MESSAGE (fallback)
        if not heading and hasattr(self.log_entry, 'MESSAGE'):
            # MESSAGE format: "HEADING | body"
            parts = self.log_entry.MESSAGE.split('|', 1)
            if parts:
                heading = parts[0].strip().upper()

        # Default to OTHER
        determined_category = LogCategory.OTHER

        # Build keyword map based on only_for_custom flag
        if only_for_custom:
            # Only use custom routes
            keyword_map = self._custom_routes
        else:
            # Merge default + custom (custom overrides default if same keyword)
            keyword_map = {**self.DEFAULT_KEYWORD_MAP, **self._custom_routes}

        # Match keywords in heading (first match wins)
        for keyword, category in keyword_map.items():
            if keyword.upper() in heading:
                # Ensure category is LogCategory enum (handle both enum and string)
                if isinstance(category, str):
                    try:
                        determined_category = LogCategory[category.upper()]
                    except KeyError:
                        # Invalid category string, skip
                        continue
                elif isinstance(category, LogCategory):
                    determined_category = category
                else:
                    # Unknown type, skip
                    continue

                # First match wins, stop searching
                break

        # Set the LOG_TYPE on the log entry
        self.log_entry.LOG_TYPE = determined_category
        return self.log_entry


    def get_appropriate_handlers(self):
        """
        Retrieve handlers that are appropriate for the determined log entry LOG_TYPE.
        :return: list: A list of handlers suitable for the log entry's LOG_TYPE.
        """
        for handler in self.handlers:
            if handler.should_handle(self.log_entry):
                yield handler
