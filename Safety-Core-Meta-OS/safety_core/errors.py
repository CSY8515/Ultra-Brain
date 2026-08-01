"""Typed Safety Core failures.

Errors are deliberately narrow so callers can fail closed without parsing
exception text.  No exception contains request payloads or secret values.
"""


class SafetyCoreError(Exception):
    """Base class for all Safety Core failures."""


class ValidationError(SafetyCoreError):
    """Input or artifact validation failed."""


class IntegrityError(SafetyCoreError):
    """Integrity evidence could not be established."""


class UnsafePathError(SafetyCoreError):
    """A path escaped or could escape its declared boundary."""


class LedgerError(SafetyCoreError):
    """The append-only audit ledger is missing, corrupt, or not writable."""


class PolicyError(SafetyCoreError):
    """A safety policy is missing, malformed, or unsupported."""


class StateTransitionError(SafetyCoreError):
    """An incident state transition is not permitted."""


class RecoveryError(SafetyCoreError):
    """Backup verification or non-destructive recovery failed."""
