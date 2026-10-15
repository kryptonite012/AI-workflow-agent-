"""
Centralized timestamp utility for consistent timestamp formatting across the logging system.
Format: dd-mm-yyyy hh:mm:ss.milliseconds AM/PM
"""
from datetime import datetime


def get_formatted_timestamp() -> str:
    """
    Get current timestamp in standardized format.

    Format: dd-mm-yyyy hh:mm:ss.milliseconds AM/PM
    Example: 01-01-2026 04:30:15.234 PM

    Returns:
        str: Formatted timestamp string
    """
    now = datetime.now()
    # Format: dd-mm-yyyy hh:mm:ss.milliseconds AM/PM
    return now.strftime("%d-%m-%Y %I:%M:%S.%f")[:-3] ## + now.strftime(" %p") ## this is not serializable

