from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .ast_nodes import (
    Action,
    Automation,
    ChooseAction,
    ChooseCase,
    Condition,
    DelayAction,
    DeviceAction,
    DeviceCondition,
    DeviceDeclaration,
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
    infer_domain_from_dotted_name,
)
from .diagnostics import Diagnostic
from .symbol_table import SymbolTable, VALID_DOMAINS


ALLOWED_TOGGLE_DOMAINS = {"light", "switch", "cover"}
ALLOWED_OPEN_CLOSE_DOMAINS = {"cover"}
VALID_MODES = {"single", "restart"}
VALID_SUN_EVENTS = {"sunrise", "sunset"}
TEXTUAL_SERVICE_KEYS = {"message", "title", "text", "text_command", "sound"}


@dataclass
class SemanticAnalyzer:
    symbol_table: SymbolTable = field(default_factory=SymbolTable)
    diagnostics: list[Diagnostic] = field(default_factory=list)

    def analyze(self, program: ProgramNode) -> list[Diagnostic]:
        self.diagnostics.clear()
        self.symbol_table = SymbolTable()

        self._register_declarations(program)
        for automation in program.automations:
            self._analyze_automation(automation)

        return list(self.diagnostics)

    def _register_declarations(self, program: ProgramNode) -> None:
        for declaration in program.declarations:
            if isinstance(declaration, DeviceDeclaration):
                if declaration.name in self.symbol_table.devices or declaration.name in self.symbol_table.entities:
                    self._error(f"Duplicate declaration for '{declaration.name}'.")
                    continue
                if not self._is_valid_domain(declaration.domain):
                    self._error(f"Unknown domain '{declaration.domain}' in device declaration '{declaration.name}'.")
                entity_domain = infer_domain_from_dotted_name(declaration.entity_id)
                if entity_domain is not None and entity_domain != declaration.domain:
                    self._error(
                        f"Device declaration '{declaration.name}' has entity_id incompatible with domain '{declaration.domain}'."
                    )
                self.symbol_table.define_device(declaration)
                continue

            if declaration.name in self.symbol_table.entities or declaration.name in self.symbol_table.devices:
                self._error(f"Duplicate declaration for '{declaration.name}'.")
                continue

            if declaration.domain is None or not self._is_valid_domain(declaration.domain):
                self._error(f"Unknown domain in entity declaration '{declaration.name}'.")
            self.symbol_table.define_entity(declaration)

    def _analyze_automation(self, automation: Automation) -> None:
        if automation.mode not in VALID_MODES:
            self._error(f"Automation '{automation.alias}' uses invalid mode '{automation.mode}'.")

        trigger_ids = self._collect_trigger_ids(automation)

        for trigger in automation.triggers:
            self._analyze_trigger(trigger, automation.alias)

        for condition in automation.conditions:
            self._analyze_condition(condition, trigger_ids)

        for action in automation.actions:
            self._analyze_action(action, trigger_ids)

    def _collect_trigger_ids(self, automation: Automation) -> set[str]:
        result: set[str] = set()
        for trigger in automation.triggers:
            trigger_id = getattr(trigger, "trigger_id", None)
            if trigger_id:
                result.add(trigger_id)
        return result

    def _analyze_trigger(self, trigger: Any, automation_alias: str) -> None:
        if isinstance(trigger, StateTrigger):
            if not trigger.entity_ids:
                self._error(f"Automation '{automation_alias}' has state trigger without entity_ids.")
            for entity_id in trigger.entity_ids:
                self._validate_entity_reference(entity_id, allow_symbolic=True)
            if not trigger.to_states and not trigger.from_states:
                self._error(f"Automation '{automation_alias}' has state trigger without target or source state.")
            return

        if isinstance(trigger, DeviceTrigger):
            resolved = self.symbol_table.resolve_device_reference(trigger.domain, trigger.device_id, trigger.entity_id)
            if resolved is None:
                self._error("Device trigger requires declared device alias or inline domain/device_id/entity_id.")
                return
            if not self._is_valid_domain(resolved.domain):
                self._error(f"Device trigger uses unknown domain '{resolved.domain}'.")
            if trigger.device_type in {"bateria", "volume_fluxo"}:
                if resolved.domain != "sensor":
                    self._error(f"Trigger '{trigger.device_type}' requires domain 'sensor'.")
                if not self._is_numeric_literal(trigger.above) and not self._is_numeric_literal(trigger.below):
                    self._error(f"Trigger '{trigger.device_type}' requires numeric above or below threshold.")
            return

        if isinstance(trigger, SunTrigger):
            if trigger.event not in VALID_SUN_EVENTS:
                self._error(f"Sun trigger uses invalid event '{trigger.event}'.")
            return

        if isinstance(trigger, TimeTrigger):
            if not self._is_valid_time(trigger.at):
                self._error(f"Time trigger uses invalid time '{trigger.at}'.")
            return

    def _analyze_condition(self, condition: Condition, trigger_ids: set[str]) -> None:
        if isinstance(condition, StateCondition):
            self._validate_entity_reference(condition.entity_id, allow_symbolic=True)
            return

        if isinstance(condition, DeviceCondition):
            resolved = self.symbol_table.resolve_device_reference(
                condition.domain,
                condition.device_id,
                condition.entity_id,
            )
            if resolved is None:
                self._error("Device condition requires domain, device_id and entity_id or a declared device alias.")
                return
            if not condition.condition_type:
                self._error("Device condition requires a condition_type.")
            return

        if isinstance(condition, TriggerCondition):
            for trigger_id in condition.ids:
                if trigger_id not in trigger_ids:
                    self._error(f"Unknown trigger id '{trigger_id}' referenced in condition.")
            return

        if isinstance(condition, TimeCondition):
            if condition.after is not None and not self._is_valid_time(condition.after):
                self._error(f"Time condition uses invalid time '{condition.after}'.")
            if condition.before is not None and not self._is_valid_time(condition.before):
                self._error(f"Time condition uses invalid time '{condition.before}'.")
            return

        if isinstance(condition, SunCondition):
            if condition.before is not None and condition.before not in VALID_SUN_EVENTS:
                self._error(f"Sun condition uses invalid before event '{condition.before}'.")
            if condition.after is not None and condition.after not in VALID_SUN_EVENTS:
                self._error(f"Sun condition uses invalid after event '{condition.after}'.")
            return

        if isinstance(condition, LogicalCondition):
            if condition.operator not in {"and", "or"}:
                self._error(f"Logical condition uses invalid operator '{condition.operator}'.")
            for child in condition.conditions:
                self._analyze_condition(child, trigger_ids)

    def _analyze_action(self, action: Action, trigger_ids: set[str]) -> None:
        if isinstance(action, DeviceAction):
            resolved = self.symbol_table.resolve_device_reference(action.domain, action.device_id, action.entity_id)
            if resolved is None:
                self._error("Device action requires declared device alias or inline domain/device_id/entity_id.")
                return
            if action.action_type in {"ligar", "desligar", "alternar", "turn_on", "turn_off", "toggle"}:
                if resolved.domain not in ALLOWED_TOGGLE_DOMAINS:
                    self._error(
                        f"Action '{action.action_type}' is not compatible with domain '{resolved.domain}'."
                    )
            if action.action_type in {"abrir", "fechar", "open", "close"} and resolved.domain not in ALLOWED_OPEN_CLOSE_DOMAINS:
                self._error(
                    f"Action '{action.action_type}' is only compatible with domain 'cover', not '{resolved.domain}'."
                )
            return

        if isinstance(action, ServiceAction):
            self._analyze_service_action(action)
            return

        if isinstance(action, DelayAction):
            if not action.duration.raw:
                self._error("Delay action requires a duration.")
            return

        if isinstance(action, IfAction):
            for condition in action.conditions:
                self._analyze_condition(condition, trigger_ids)
            for nested in action.then_actions:
                self._analyze_action(nested, trigger_ids)
            for nested in action.else_actions:
                self._analyze_action(nested, trigger_ids)
            return

        if isinstance(action, ChooseAction):
            for case in action.cases:
                self._analyze_choose_case(case, trigger_ids)

    def _analyze_choose_case(self, case: ChooseCase, trigger_ids: set[str]) -> None:
        for condition in case.conditions:
            self._analyze_condition(condition, trigger_ids)
        for action in case.sequence:
            self._analyze_action(action, trigger_ids)

    def _analyze_service_action(self, action: ServiceAction) -> None:
        service_domain = infer_domain_from_dotted_name(action.service)
        if service_domain is None or not self._is_valid_domain(service_domain):
            self._error(f"Service '{action.service}' uses unknown domain.")
            return

        if action.service in {"timer.start", "timer.finish"}:
            if not action.target_entity_ids:
                self._error(f"Service '{action.service}' requires timer targets.")
            for entity_id in action.target_entity_ids:
                resolved = self._validate_entity_reference(entity_id, allow_symbolic=True)
                if resolved is not None and resolved.domain != "timer":
                    self._error(f"Service '{action.service}' only accepts targets in domain 'timer'.")

        if action.service == "automation.trigger":
            if not action.target_entity_ids:
                self._error("Service 'automation.trigger' requires automation targets.")
            for entity_id in action.target_entity_ids:
                resolved = self._validate_entity_reference(entity_id, allow_symbolic=True)
                if resolved is not None and resolved.domain != "automation":
                    self._error("Service 'automation.trigger' only accepts targets in domain 'automation'.")

        if action.service in {"media_player.turn_off", "media_player.volume_set", "media_player.play_media"}:
            if not action.target_entity_ids and not action.target_device_ids:
                self._error(f"Service '{action.service}' requires media_player targets or device_id.")
            for entity_id in action.target_entity_ids:
                resolved = self._validate_entity_reference(entity_id, allow_symbolic=True)
                if resolved is not None and resolved.domain != "media_player":
                    self._error(f"Service '{action.service}' only accepts media_player targets.")

        if action.service.startswith("notify.") or action.service == "tts.speak":
            if not self._has_textual_payload(action.data):
                self._error(f"Service '{action.service}' requires textual data.")

        if action.service == "alexa_devices.send_text_command":
            if not isinstance(action.data.get("device_id"), str) or not isinstance(action.data.get("text_command"), str):
                self._error("Service 'alexa_devices.send_text_command' requires data.device_id and data.text_command.")

        if action.service == "alexa_devices.send_sound":
            if not isinstance(action.data.get("device_id"), str) or not isinstance(action.data.get("sound"), str):
                self._error("Service 'alexa_devices.send_sound' requires data.device_id and data.sound.")

    def _validate_entity_reference(self, entity_id: str, allow_symbolic: bool) -> Any:
        resolved = self.symbol_table.resolve_entity_reference(entity_id)
        if resolved is None:
            if allow_symbolic and "." not in entity_id:
                self._error(f"Undefined entity symbol '{entity_id}'.")
                return None
            self._error(f"Invalid entity reference '{entity_id}'.")
            return None

        if not self._is_valid_domain(resolved.domain):
            self._error(f"Entity reference '{resolved.entity_id}' uses unknown domain '{resolved.domain}'.")
        return resolved

    @staticmethod
    def _is_valid_domain(domain: str | None) -> bool:
        return domain in VALID_DOMAINS

    @staticmethod
    def _is_numeric_literal(value: LiteralValue | None) -> bool:
        return value is not None and isinstance(value.value, (int, float))

    @staticmethod
    def _is_valid_time(value: str) -> bool:
        parts = value.split(":")
        if len(parts) != 3 or not all(part.isdigit() for part in parts):
            return False
        hour, minute, second = (int(part) for part in parts)
        return 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59

    @staticmethod
    def _has_textual_payload(data: dict[str, Any]) -> bool:
        for key, value in data.items():
            if key in TEXTUAL_SERVICE_KEYS and isinstance(value, str):
                return True
            if isinstance(value, dict) and SemanticAnalyzer._has_textual_payload(value):
                return True
            if isinstance(value, list):
                if any(isinstance(item, str) for item in value):
                    return True
                if any(isinstance(item, dict) and SemanticAnalyzer._has_textual_payload(item) for item in value):
                    return True
        return False

    def _error(self, message: str, line: int = 1, column: int = 1) -> None:
        self.diagnostics.append(Diagnostic(message=message, line=line, column=column))
