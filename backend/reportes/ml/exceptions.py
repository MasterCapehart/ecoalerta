class PredictionModelNotReady(RuntimeError):
    """Raised when the ML model cannot be trained or loaded."""


class PredictionModelNotFound(FileNotFoundError):
    """Raised when the persisted ML model artifact is missing."""

