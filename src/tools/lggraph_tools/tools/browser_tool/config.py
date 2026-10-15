"""
configuration file for the browser tool that is required or options also
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any


@dataclass
class BrowserRequiredConfig:
    """
    Configuration for the browser tool Runner.

    Required:
        query: The task/query to execute in the browser

    Optional:
        All other fields have sensible defaults
    """
    # required configurations to perform task from the browser agent
    query: str

    # File paths (optional - will use defaults from settings if not provided)
    file_path: Optional[Path] = field(default=None)  # Legacy field for compatibility
    result_file: Optional[str] = field(default=None)  # Path to write result JSON

    # optional configurations for the browser agent
    headless: bool = field(default=False)  # these are in fields because these are the user defined settings
    log: bool = field(default=True)
    keep_alive: bool = field(default=True)

    # some browser agent level settings
    max_failures: int = 5
    max_steps: int = 500
    vision_detail_level: str = 'high'

    # Recording
    record_video: bool = True
    video_dir: Optional[Path] = field(default=None)  # if None it would use the default temp directory of the browser agent

    # user data handling
    user_data_dir: Optional[Path] = field(default=None)  # if None it would use the default temp directory of the browser agent

    # Timeouts
    browser_ready_timeout: int = 30
    task_timeout: int = 1300
    timeout: int = 1300  # Alias for task_timeout for compatibility

    extra_options: Optional[Dict[str, Any]] = field(default=None)  # please read the kwargs in the browser tool runner for more details
