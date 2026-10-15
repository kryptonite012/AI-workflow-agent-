import json

from src.utils.timestamp_util import get_formatted_timestamp


class ProtocolAdapter:
    """
    convert the debug protocol log entry to LogEntry object for the appropriate logs handling.
    """
    @staticmethod
    def convert_to_log_entry_json(debug_message_json: str) -> str:
        try:
            debug_data = json.loads(debug_message_json)

            # Extract fields
            data = debug_data.get("data", {})
            timestamp = debug_data.get("timestamp", get_formatted_timestamp())

            # PRESERVE HEADING IN METADATA (Don't lose it!)
            metadata = data.get("metadata", {})
            metadata["heading"] = data.get("heading", "")  # ← KEY FIX!
            metadata["body"] = data.get("body", "")  # ← KEY FIX!

            # Simple field mapping (no logic!)
            log_entry = {
                "LOG_TYPE": "OTHER",  # ← Default, Router will fix this later
                "LEVEL": data.get("level", "INFO"),  # ← Simple copy
                "MESSAGE": f"{data.get('heading', '')} | {data.get('body', '')}",
                "TIME_STAMP": timestamp,
                "METADATA": metadata  # ← NOW contains heading!
            }

            return json.dumps(log_entry, ensure_ascii=False)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")