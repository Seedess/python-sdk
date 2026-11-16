"""Official Seedess SDK for Python (server-side)."""

from .client import Seedess
from .errors import SeedessError

__all__ = ["Seedess", "SeedessError"]
__version__ = "0.1.0"
