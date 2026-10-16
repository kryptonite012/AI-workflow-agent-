"""Top-level src package.

Purposely keeps initialization minimal to avoid circular imports.
Import subpackages explicitly, e.g.:
    from src.utils import model_manager
    from src.config import settings

No implicit re-export of heavy modules to keep startup fast and predictable.
"""
import os, sys


# Ensure parent package (project root) is on sys.path for running as script
_parent_dir = os.path.dirname(os.path.abspath(__file__))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

if __name__ == '__main__':
    print(_parent_dir)
