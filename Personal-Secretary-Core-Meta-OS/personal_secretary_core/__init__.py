"""Public API for Personal Secretary Core Meta OS v0.6."""

from .core import PersonalSecretaryCore
from .models import *
from .validation import AuthorizationError, ValidationError

__version__ = "0.6.0"
__all__ = ["PersonalSecretaryCore", "AuthorizationError", "ValidationError"]
