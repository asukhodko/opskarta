class OpskartaError(Exception):
    """Base exception for opskarta."""


class ValidationError(OpskartaError):
    """Raised when an opskarta file is invalid."""


class SchedulingError(OpskartaError):
    """Raised when scheduling can't be computed (missing dates, cycles, etc.)."""
