from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TaskState(str, Enum):
    """Represents the current state."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(BaseModel):
    """Represents the current status of a background download task."""

    task_id: UUID
    state: TaskState
    progress: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Progress percentage 0-100"
    )
    message: Optional[str] = Field(None, description="Status message or error detail")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @property
    def is_terminal(self) -> bool:
        return self.state in (
            TaskState.COMPLETED,
            TaskState.FAILED,
            TaskState.CANCELLED,
        )


if __name__ == "__main__":
    pass
