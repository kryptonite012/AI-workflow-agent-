"""Cross-platform notification beep.

`winsound` only exists on Windows; importing it unconditionally breaks the
whole application on Linux and macOS. Use `beep()` instead.
"""
import sys

try:
    import winsound  # type: ignore[import-not-found]
except ImportError:  # Linux / macOS
    winsound = None


def beep(frequency: int, duration_ms: int) -> None:
    """Play a beep. Uses winsound on Windows, the terminal bell elsewhere."""
    try:
        if winsound is not None:
            winsound.Beep(frequency, duration_ms)
        elif sys.stdout is not None and sys.stdout.isatty():
            sys.stdout.write("\a")
            sys.stdout.flush()
    except Exception:
        # A missing sound device must never break the caller
        pass
