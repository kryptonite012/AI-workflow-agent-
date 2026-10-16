"""
defines the interface for log formatters in a structured system_logging system.
===========================================================
"""

from abc import ABC, abstractmethod
from typing import Any

from .protocol import LogEntry

#=========================================
# Define the OutPutFormater interface
#=========================================
class OutPutFormater(ABC):
    @abstractmethod
    def format(self, log_entry: LogEntry, *args) -> Any:
        """
        Format a log entry into a string representation.

        Args:
            log_entry : The log entry to format.

        Returns:
            str: The formatted log entry as a string.
        """
        raise NotImplementedError



# ===========================================
# text formater implementation
# ==========================================
class TextFormater(OutPutFormater):
    @classmethod
    def format(cls, log_entry: LogEntry, *args) -> str:
        """
        Format a log entry into a plain text representation.

        Args:
            log_entry : The log entry to format.

        Returns:
            str: The formatted log entry as a plain text string.
        """


        """
        desired output example:
        
        [2025-11-09 16:45:23.123] INFO | Agent.InitialPlanner
          Plan generated successfully
          Tasks: 7
          Tool: list_directory
        
        """
        metadata_str = (
            ", ".join(f"{key}={value}" for key, value in log_entry.METADATA.items())
            if log_entry.METADATA
            else "No Metadata"
        )
        return (
            f"[{log_entry.TIME_STAMP}]"
            f"\t{log_entry.LOG_LEVEL.value} - {log_entry.LOG_TYPE.value}: "
            f"\t{log_entry.MESSAGE} "
            f"\tMetadata: [ {metadata_str} ]"
        )
