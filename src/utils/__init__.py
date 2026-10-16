"""Unified utils package initializer.

Provides a stable, minimal public API and defers heavy imports until
first attribute access to reduce circular import risk and startup cost.

Public API (lazy for heavy modules):
    debug_helpers
    debug_message_protocol
    rich_traceback_manager
    open_ai_integration (lazy)
    model_manager (lazy)
    socket_manager (lazy)

Backward Compatibility:
    Older code may attempt: `import src.utils.debug_message_protocol` or
    `import src.utils.debug_helpers`. We register lightweight aliases in
    sys.modules so those imports succeed without reintroducing the old
    heavy eager import pattern.
"""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Dict
import sys

__all__ = [
    "debug_helpers",
    "debug_message_protocol",
    "rich_traceback_manager",
    "open_ai_integration",
    "model_manager",
    "socket_manager",
]

_LAZY_MODULES: Dict[str, str] = {
    "open_ai_integration": "src.utils.open_ai_integration",
    "model_manager": "src.utils.model_manager",
    "socket_manager": "src.utils.socket_manager",
}

# Lightweight eager imports (small & safe):
try:  # debug helpers
    debug_helpers = import_module("src.ui.diagnostics.debug_helpers")  # type: ignore
except Exception:  # pragma: no cover
    debug_helpers = None  # type: ignore

try:  # message protocol
    debug_message_protocol = import_module("src.ui.diagnostics.debug_message_protocol")  # type: ignore
except Exception:  # pragma: no cover
    debug_message_protocol = None  # type: ignore

try:  # traceback manager
    rich_traceback_manager = import_module("src.ui.diagnostics.rich_traceback_manager")  # type: ignore
except Exception:  # pragma: no cover
    rich_traceback_manager = None  # type: ignore

# Register backward-compatible aliases ONLY if available
if debug_message_protocol is not None:
    sys.modules.setdefault("src.utils.debug_message_protocol", debug_message_protocol)  # type: ignore
if debug_helpers is not None:
    sys.modules.setdefault("src.utils.debug_helpers", debug_helpers)  # type: ignore

_LEGACY_ATTRIBUTE_MAP = {
    # future: "old_name": "new_name"
}


def __getattr__(name: str) -> ModuleType:  # noqa: D401
    """Lazily load registered heavy utility submodules."""
    if name in _LEGACY_ATTRIBUTE_MAP:
        name = _LEGACY_ATTRIBUTE_MAP[name]
    if name in _LAZY_MODULES:
        path = _LAZY_MODULES[name]
        try:
            mod = import_module(path)
            globals()[name] = mod  # cache
            return mod  # type: ignore
        except Exception as e:  # pragma: no cover
            raise AttributeError(f"Failed lazy import '{name}' ({path}): {e}") from e
    raise AttributeError(f"module 'src.utils' has no attribute '{name}'")


def __dir__():  # pragma: no cover
    return sorted(set(__all__ + [k for k in globals().keys() if not k.startswith("_")]))
