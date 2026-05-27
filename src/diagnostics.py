from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(slots=True, frozen=True)
class Diagnostic:
    message: str
    line: int
    column: int
    severity: Severity = Severity.ERROR

    def __str__(self) -> str:
        return f"{self.severity.value.upper()} {self.line}:{self.column} {self.message}"
