from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, TypeAlias


class ASTNode:
    """Base class with compact debug-friendly string formatting."""

    def __repr__(self) -> str:
        parts: list[str] = []
        for item in fields(self):
            value = getattr(self, item.name)
            if value in (None, [], {}, ""):
                continue
            parts.append(f"{item.name}={value!r}")
        joined = ", ".join(parts)
        return f"{self.__class__.__name__}({joined})"

    __str__ = __repr__


def infer_domain_from_dotted_name(name: str) -> str | None:
    if "." not in name:
        return None
    domain, _, _ = name.partition(".")
    return domain or None


@dataclass(slots=True, repr=False)
class LiteralValue(ASTNode):
    value: str | int | float | bool | list[Any] | dict[str, Any]


@dataclass(slots=True, repr=False)
class Duration(ASTNode):
    raw: str


@dataclass(slots=True, repr=False)
class EntityDeclaration(ASTNode):
    name: str
    entity_id: str
    domain: str | None = None

    def __post_init__(self) -> None:
        if self.domain is None:
            self.domain = infer_domain_from_dotted_name(self.entity_id)


@dataclass(slots=True, repr=False)
class DeviceDeclaration(ASTNode):
    name: str
    domain: str
    device_id: str
    entity_id: str


@dataclass(slots=True, repr=False)
class StateTrigger(ASTNode):
    entity_ids: list[str]
    to_states: list[LiteralValue]
    from_states: list[LiteralValue] | None = None
    trigger_id: str | None = None
    alias: str | None = None
    for_duration: Duration | None = None


@dataclass(slots=True, repr=False)
class DeviceTrigger(ASTNode):
    domain: str
    device_id: str
    entity_id: str
    device_type: str
    trigger_id: str | None = None
    above: LiteralValue | None = None
    below: LiteralValue | None = None
    for_duration: Duration | None = None


@dataclass(slots=True, repr=False)
class SunTrigger(ASTNode):
    event: str
    offset: str | None = None
    trigger_id: str | None = None


@dataclass(slots=True, repr=False)
class TimeTrigger(ASTNode):
    at: str
    trigger_id: str | None = None
    weekdays: list[str] | None = None


@dataclass(slots=True, repr=False)
class StateCondition(ASTNode):
    entity_id: str
    states: list[LiteralValue]
    enabled: bool | None = None


@dataclass(slots=True, repr=False)
class DeviceCondition(ASTNode):
    domain: str
    device_id: str
    entity_id: str
    condition_type: str
    enabled: bool | None = None


@dataclass(slots=True, repr=False)
class TriggerCondition(ASTNode):
    ids: list[str]
    enabled: bool | None = None


@dataclass(slots=True, repr=False)
class TimeCondition(ASTNode):
    after: str | None = None
    before: str | None = None
    weekdays: list[str] | None = None
    enabled: bool | None = None


@dataclass(slots=True, repr=False)
class SunCondition(ASTNode):
    before: str | None = None
    after: str | None = None
    enabled: bool | None = None


@dataclass(slots=True, repr=False)
class LogicalCondition(ASTNode):
    operator: str
    conditions: list["Condition"]
    enabled: bool | None = None


@dataclass(slots=True, repr=False)
class DeviceAction(ASTNode):
    domain: str
    device_id: str
    entity_id: str
    action_type: str
    brightness_pct: int | None = None
    enabled: bool | None = None


@dataclass(slots=True, repr=False)
class ServiceAction(ASTNode):
    service: str
    target_entity_ids: list[str] = field(default_factory=list)
    target_device_ids: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    enabled: bool | None = None


@dataclass(slots=True, repr=False)
class DelayAction(ASTNode):
    duration: Duration


@dataclass(slots=True, repr=False)
class IfAction(ASTNode):
    conditions: list["Condition"]
    then_actions: list["Action"]
    else_actions: list["Action"] = field(default_factory=list)


@dataclass(slots=True, repr=False)
class ChooseCase(ASTNode):
    conditions: list["Condition"]
    sequence: list["Action"]


@dataclass(slots=True, repr=False)
class ChooseAction(ASTNode):
    cases: list[ChooseCase]


Trigger: TypeAlias = StateTrigger | DeviceTrigger | SunTrigger | TimeTrigger
Condition: TypeAlias = (
    StateCondition
    | DeviceCondition
    | TriggerCondition
    | TimeCondition
    | SunCondition
    | LogicalCondition
)
Action: TypeAlias = DeviceAction | ServiceAction | DelayAction | IfAction | ChooseAction
Declaration: TypeAlias = EntityDeclaration | DeviceDeclaration


@dataclass(slots=True, repr=False)
class Automation(ASTNode):
    alias: str
    description: str = ""
    mode: str = "single"
    triggers: list[Trigger] = field(default_factory=list)
    conditions: list[Condition] = field(default_factory=list)
    actions: list[Action] = field(default_factory=list)

    @property
    def name(self) -> str:
        return self.alias


@dataclass(slots=True, repr=False)
class Program(ASTNode):
    declarations: list[Declaration] = field(default_factory=list)
    automations: list[Automation] = field(default_factory=list)


# Compatibility aliases for the current parser/bootstrap code.
ProgramNode = Program
AutomationNode = Automation
