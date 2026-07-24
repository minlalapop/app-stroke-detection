import enum


class ModelExecutionStatus(str, enum.Enum):
    READY = "READY"
    COMPLETED = "COMPLETED"
    MODEL_NOT_AVAILABLE = "MODEL_NOT_AVAILABLE"
    FAILED = "FAILED"
