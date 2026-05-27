from __future__ import annotations

from typing import Any

import yaml

from .ast_nodes import (
    Action,
    Automation,
    ChooseAction,
    ChooseCase,
    Condition,
    DelayAction,
    DeviceAction,
    DeviceCondition,
    DeviceTrigger,
    IfAction,
    LiteralValue,
    LogicalCondition,
    ProgramNode,
    ServiceAction,
    StateCondition,
    StateTrigger,
    SunCondition,
    SunTrigger,
    TimeCondition,
    TimeTrigger,
    TriggerCondition,
    DeviceDeclaration,
    EntityDeclaration,
)


DEVICE_TRIGGER_TYPE_MAP = {
    "ligado": "turned_on",
    "desligado": "turned_off",
    "movimento": "motion",
    "aberta": "opened",
    "aberto": "opened",
    "fechada": "not_opened",
    "fechado": "not_opened",
}

DEVICE_ACTION_TYPE_MAP = {
    "ligar": "turn_on",
    "desligar": "turn_off",
    "alternar": "toggle",
    "abrir": "open",
    "fechar": "close",
    "turn_on": "turn_on",
    "turn_off": "turn_off",
    "toggle": "toggle",
    "open": "open",
    "close": "close",
}

DEVICE_CONDITION_TYPE_MAP = {
    "ligado": "is_on",
    "desligado": "is_off",
    "aberto": "is_open",
    "aberta": "is_open",
    "fechado": "is_closed",
    "fechada": "is_closed",
    "armado": "is_armed",
    "desarmado": "is_disarmed",
}

SUN_EVENT_MAP = {
    "sunrise": "sunrise",
    "sunset": "sunset",
    "nascer_do_sol": "sunrise",
    "por_do_sol": "sunset",
}


def generate_yaml(program: ProgramNode) -> str:
    context = _build_resolution_context(program)
    payload = [_emit_automation(automation, context) for automation in program.automations]
    yaml_text = yaml.safe_dump(
        payload,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
    yaml.safe_load(yaml_text)
    return yaml_text


def _build_resolution_context(program: ProgramNode) -> dict[str, dict[str, Any]]:
    entities: dict[str, str] = {}
    devices: dict[str, dict[str, str]] = {}
    for declaration in program.declarations:
        if isinstance(declaration, EntityDeclaration):
            entities[declaration.name] = declaration.entity_id
        elif isinstance(declaration, DeviceDeclaration):
            devices[declaration.name] = {
                "domain": declaration.domain,
                "device_id": declaration.device_id,
                "entity_id": declaration.entity_id,
            }
    return {"entities": entities, "devices": devices}


def _emit_automation(automation: Automation, context: dict[str, dict[str, Any]]) -> dict[str, Any]:
    item: dict[str, Any] = {
        "alias": automation.alias,
        "description": automation.description,
        "triggers": [_emit_trigger(trigger, context) for trigger in automation.triggers],
        "conditions": [_emit_condition(condition, context) for condition in automation.conditions],
        "actions": [_emit_action(action, context) for action in automation.actions],
        "mode": automation.mode,
    }
    return item


def _emit_trigger(trigger: Any, context: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if isinstance(trigger, StateTrigger):
        item: dict[str, Any] = {
            "trigger": "state",
            "entity_id": [_resolve_entity_ref(entity_id, context) for entity_id in trigger.entity_ids],
            "to": _emit_literal_list(trigger.to_states),
        }
        if trigger.from_states:
            item["from"] = _emit_literal_list(trigger.from_states)
        if trigger.trigger_id:
            item["id"] = trigger.trigger_id
        if trigger.alias:
            item["alias"] = trigger.alias
        if trigger.for_duration:
            item["for"] = _emit_duration_dict(trigger.for_duration.raw)
        return item

    if isinstance(trigger, DeviceTrigger):
        domain, device_id, entity_id = _resolve_device_fields(
            trigger.domain,
            trigger.device_id,
            trigger.entity_id,
            context,
        )
        item = {
            "trigger": "device",
            "domain": domain,
            "device_id": device_id,
            "entity_id": entity_id,
        }
        item.update(_emit_device_trigger_type(trigger))
        if trigger.trigger_id:
            item["id"] = trigger.trigger_id
        if trigger.for_duration:
            item["for"] = _emit_duration_dict(trigger.for_duration.raw)
        return item

    if isinstance(trigger, SunTrigger):
        item = {
            "trigger": "sun",
            "event": SUN_EVENT_MAP.get(trigger.event, trigger.event),
        }
        if trigger.offset is not None:
            item["offset"] = trigger.offset
        if trigger.trigger_id:
            item["id"] = trigger.trigger_id
        return item

    if isinstance(trigger, TimeTrigger):
        item = {
            "trigger": "time",
            "at": trigger.at,
        }
        if trigger.weekdays:
            item["weekday"] = list(trigger.weekdays)
        if trigger.trigger_id:
            item["id"] = trigger.trigger_id
        return item

    raise TypeError(f"Unsupported trigger type: {type(trigger)!r}")


def _emit_device_trigger_type(trigger: DeviceTrigger) -> dict[str, Any]:
    if trigger.device_type == "bateria":
        item: dict[str, Any] = {"type": "battery_level"}
        if trigger.above is not None:
            item["above"] = _emit_literal_value(trigger.above)
        if trigger.below is not None:
            item["below"] = _emit_literal_value(trigger.below)
        return item

    if trigger.device_type == "volume_fluxo":
        item = {"type": "volume_flow_rate"}
        if trigger.above is not None:
            item["above"] = _emit_literal_value(trigger.above)
        if trigger.below is not None:
            item["below"] = _emit_literal_value(trigger.below)
        return item

    return {"type": DEVICE_TRIGGER_TYPE_MAP.get(trigger.device_type, trigger.device_type)}


def _emit_condition(condition: Condition, context: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if isinstance(condition, StateCondition):
        item = {
            "condition": "state",
            "entity_id": _resolve_entity_ref(condition.entity_id, context),
            "state": _emit_scalar_or_list(condition.states),
        }
        if condition.enabled is not None:
            item["enabled"] = condition.enabled
        return item

    if isinstance(condition, DeviceCondition):
        domain, device_id, entity_id = _resolve_device_fields(
            condition.domain,
            condition.device_id,
            condition.entity_id,
            context,
        )
        item = {
            "condition": "device",
            "domain": domain,
            "device_id": device_id,
            "entity_id": entity_id,
            "type": DEVICE_CONDITION_TYPE_MAP.get(condition.condition_type, condition.condition_type),
        }
        if condition.enabled is not None:
            item["enabled"] = condition.enabled
        return item

    if isinstance(condition, TriggerCondition):
        item = {
            "condition": "trigger",
            "id": condition.ids if len(condition.ids) > 1 else condition.ids[0],
        }
        if condition.enabled is not None:
            item["enabled"] = condition.enabled
        return item

    if isinstance(condition, TimeCondition):
        item: dict[str, Any] = {"condition": "time"}
        if condition.after is not None:
            item["after"] = condition.after
        if condition.before is not None:
            item["before"] = condition.before
        if condition.weekdays:
            item["weekday"] = list(condition.weekdays)
        if condition.enabled is not None:
            item["enabled"] = condition.enabled
        return item

    if isinstance(condition, SunCondition):
        item = {"condition": "sun"}
        if condition.before is not None:
            item["before"] = SUN_EVENT_MAP.get(condition.before, condition.before)
        if condition.after is not None:
            item["after"] = SUN_EVENT_MAP.get(condition.after, condition.after)
        if condition.enabled is not None:
            item["enabled"] = condition.enabled
        return item

    if isinstance(condition, LogicalCondition):
        item = {
            "condition": condition.operator,
            "conditions": [_emit_condition(child, context) for child in condition.conditions],
        }
        if condition.enabled is not None:
            item["enabled"] = condition.enabled
        return item

    raise TypeError(f"Unsupported condition type: {type(condition)!r}")


def _emit_action(action: Action, context: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if isinstance(action, DeviceAction):
        domain, device_id, entity_id = _resolve_device_fields(
            action.domain,
            action.device_id,
            action.entity_id,
            context,
        )
        item: dict[str, Any] = {
            "type": DEVICE_ACTION_TYPE_MAP.get(action.action_type, action.action_type),
            "device_id": device_id,
            "entity_id": entity_id,
            "domain": domain,
        }
        if action.brightness_pct is not None:
            item["brightness_pct"] = action.brightness_pct
        if action.enabled is not None:
            item["enabled"] = action.enabled
        return item

    if isinstance(action, ServiceAction):
        item = {
            "action": action.service,
            "target": {},
            "data": _emit_data(action.data),
        }
        if action.target_entity_ids:
            item["target"]["entity_id"] = [
                _resolve_entity_ref(entity_id, context)
                for entity_id in action.target_entity_ids
            ]
        if action.target_device_ids:
            item["target"]["device_id"] = list(action.target_device_ids)
        if not item["target"]:
            del item["target"]
        if action.metadata:
            item["metadata"] = _emit_data(action.metadata)
        if action.enabled is not None:
            item["enabled"] = action.enabled
        return item

    if isinstance(action, DelayAction):
        return {
            "delay": _emit_duration_dict(action.duration.raw),
        }

    if isinstance(action, IfAction):
        item = {
            "if": [_emit_condition(condition, context) for condition in action.conditions],
            "then": [_emit_action(child, context) for child in action.then_actions],
        }
        if action.else_actions:
            item["else"] = [_emit_action(child, context) for child in action.else_actions]
        return item

    if isinstance(action, ChooseAction):
        return {
            "choose": [_emit_choose_case(case, context) for case in action.cases],
        }

    raise TypeError(f"Unsupported action type: {type(action)!r}")


def _emit_choose_case(case: ChooseCase, context: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "conditions": [_emit_condition(condition, context) for condition in case.conditions],
        "sequence": [_emit_action(action, context) for action in case.sequence],
    }


def _resolve_entity_ref(name: str, context: dict[str, dict[str, Any]]) -> str:
    return context["entities"].get(name, name)


def _resolve_device_fields(
    domain_or_alias: str,
    device_id: str,
    entity_id: str,
    context: dict[str, dict[str, Any]],
) -> tuple[str, str, str]:
    resolved = context["devices"].get(domain_or_alias)
    if resolved is None:
        return domain_or_alias, device_id, entity_id
    return resolved["domain"], resolved["device_id"], resolved["entity_id"]


def _emit_data(data: dict[str, Any]) -> dict[str, Any]:
    emitted: dict[str, Any] = {}
    for key, value in data.items():
        emitted[key] = _emit_generic_value(value)
    return emitted


def _emit_generic_value(value: Any) -> Any:
    if isinstance(value, LiteralValue):
        return _emit_literal_value(value)
    if isinstance(value, dict):
        return {key: _emit_generic_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_emit_generic_value(item) for item in value]
    return value


def _emit_literal_list(values: list[LiteralValue]) -> list[Any]:
    return [_emit_literal_value(value) for value in values]


def _emit_scalar_or_list(values: list[LiteralValue]) -> Any:
    emitted = _emit_literal_list(values)
    if len(emitted) == 1:
        return emitted[0]
    return emitted


def _emit_literal_value(value: LiteralValue) -> Any:
    return value.value


def _emit_duration_dict(raw: str) -> dict[str, int]:
    hours = 0
    minutes = 0
    seconds = 0
    milliseconds = 0
    index = 0

    while index < len(raw):
        if not raw[index].isdigit():
            raise ValueError(f"Invalid duration literal: {raw}")

        start = index
        while index < len(raw) and raw[index].isdigit():
            index += 1
        amount = int(raw[start:index])

        unit_start = index
        while index < len(raw) and raw[index].isalpha():
            index += 1
        unit = raw[unit_start:index]

        if unit == "h":
            hours += amount
            continue
        if unit == "min":
            minutes += amount
            continue
        if unit == "s":
            seconds += amount
            continue
        if unit == "ms":
            milliseconds += amount
            continue

        raise ValueError(f"Invalid duration unit '{unit}' in {raw}")

    return {
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
        "milliseconds": milliseconds,
    }
