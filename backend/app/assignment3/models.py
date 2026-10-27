"""Validated session lifecycle contracts."""
from datetime import timezone
from typing import Literal
from uuid import UUID
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator
from datetime import datetime


class SessionStart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: UUID
    selected_skill: Literal["paced_breathing_4_6"] = "paced_breathing_4_6"
    started_at: AwareDatetime
    fewer_options: bool = False

    @field_validator("started_at")
    @classmethod
    def utc(cls, value: datetime) -> datetime:
        return value.astimezone(timezone.utc)


class SessionEnd(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["completed", "stopped", "interrupted"]
    ended_at: AwareDatetime
    measured_duration_seconds: float | None = Field(default=None, ge=0, allow_inf_nan=False)

    @field_validator("ended_at")
    @classmethod
    def utc(cls, value: datetime) -> datetime:
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def completed_duration(self) -> "SessionEnd":
        if self.status == "completed" and (self.measured_duration_seconds is None or not 60 <= self.measured_duration_seconds < 90):
            raise ValueError("Completed sessions require a measured duration from 60 to under 90 seconds.")
        return self


class Session(SessionStart):
    ended_at: AwareDatetime | None = None
    status: Literal["active", "completed", "stopped", "interrupted"]
    measured_duration_seconds: float | None = None


class ReflectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reflection: str = Field(min_length=1, max_length=300)

    @field_validator("reflection")
    @classmethod
    def trimmed(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Enter a short fictional reflection.")
        return value.strip()


class ConversationMessage(BaseModel):
    message_id: int
    session_id: UUID
    timestamp: AwareDatetime
    role: Literal["user", "assistant", "error"]
    content: str = Field(min_length=1, max_length=1000)
