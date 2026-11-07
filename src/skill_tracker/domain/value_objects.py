"""Immutable value objects that protect domain invariants."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from enum import Enum

from .errors import ValidationError

MIN_HOURS = Decimal("0.01")
MAX_HOURS = Decimal(24)
QUARTER = Decimal("0.25")


def quantise_hours(hours: Decimal) -> Decimal:
    """Round an hour amount to the nearest quarter hour."""
    return (hours / QUARTER).quantize(Decimal(1), rounding=ROUND_HALF_UP) * QUARTER


def require_text(value: object, field_name: str, *, max_length: int = 500) -> str:
    """Return a trimmed, non-empty string or raise ``ValidationError``."""
    if value is None:
        raise ValidationError(f"{field_name} is required")

    text = str(value).strip()
    if not text:
        raise ValidationError(f"{field_name} cannot be empty")
    if len(text) > max_length:
        raise ValidationError(f"{field_name} must be at most {max_length} characters")
    return text


def optional_text(value: object, *, max_length: int = 5000) -> str:
    """Return a trimmed string; ``None`` becomes the empty string."""
    if value is None:
        return ""
    text = str(value).strip()
    if len(text) > max_length:
        raise ValidationError(f"Text must be at most {max_length} characters")
    return text


class ProjectStatus(str, Enum):
    """Allowed lifecycle states for a project."""

    PLANNING = "Planning"
    ACTIVE = "Active"
    PAUSED = "Paused"
    COMPLETED = "Completed"

    @classmethod
    def parse(cls, value: object) -> ProjectStatus:
        if isinstance(value, cls):
            return value
        try:
            return cls(str(value))
        except ValueError as exc:
            allowed = ", ".join(status.value for status in cls)
            raise ValidationError(f"status must be one of: {allowed}") from exc


class TopicColor(str, Enum):
    """Palette tokens kept free of presentation concerns such as CSS classes."""

    INDIGO = "indigo"
    BLUE = "blue"
    PURPLE = "purple"
    EMERALD = "emerald"
    AMBER = "amber"
    ROSE = "rose"
    SLATE = "slate"
    CYAN = "cyan"
    PINK = "pink"

    @classmethod
    def parse(cls, value: object) -> TopicColor:
        if isinstance(value, cls):
            return value
        token = str(value or "").strip().lower()
        if token.startswith("bg-"):
            token = token.removeprefix("bg-").split("-")[0]
        try:
            return cls(token)
        except ValueError as exc:
            allowed = ", ".join(color.value for color in cls)
            raise ValidationError(f"color must be one of: {allowed}") from exc


@dataclass(frozen=True)
class StudyHours:
    """A positive amount of study time, quantised to quarter hours."""

    value: Decimal

    @classmethod
    def parse(cls, raw: object) -> StudyHours:
        try:
            hours = Decimal(str(raw))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValidationError("hours must be a number") from exc

        if not hours.is_finite():
            raise ValidationError("hours must be a finite number")
        if hours < MIN_HOURS:
            raise ValidationError(f"hours must be at least {MIN_HOURS}")
        if hours > MAX_HOURS:
            raise ValidationError(f"hours cannot exceed {MAX_HOURS} in a single session")

        return cls(quantise_hours(hours))

    def __float__(self) -> float:
        return float(self.value)


def parse_iso_date(value: object, field_name: str = "date") -> date:
    """Parse an ISO-8601 date string (``YYYY-MM-DD``)."""
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field_name} must be an ISO date (YYYY-MM-DD)") from exc


def parse_optional_iso_date(value: object, field_name: str = "date") -> date | None:
    if value is None or str(value).strip() == "":
        return None
    return parse_iso_date(value, field_name)


def optional_url(value: object, field_name: str = "url") -> str | None:
    """Return a validated ``http(s)`` URL or ``None``."""
    text = optional_text(value, max_length=2000)
    if not text:
        return None
    if not text.startswith(("http://", "https://")):
        raise ValidationError(f"{field_name} must start with http:// or https://")
    return text


@dataclass(frozen=True)
class Progress:
    """Completion ratio for a checklist of modules or tasks."""

    completed: int
    total: int

    @property
    def percentage(self) -> int:
        if self.total == 0:
            return 0
        return round(self.completed / self.total * 100)

