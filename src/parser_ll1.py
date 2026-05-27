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
    Duration,
    EntityDeclaration,
    IfAction,
    LiteralValue,
    LogicalCondition,
    Program,
    ProgramNode,
    ServiceAction,
    StateCondition,
    StateTrigger,
    SunCondition,
    SunTrigger,
    TimeCondition,
    TimeTrigger,
    TriggerCondition,
)
from .diagnostics import Diagnostic
from .grammar import ENDMARKER, EPSILON, NON_TERMINALS, START_SYMBOL, TERMINALS
from .parser_table import PredictiveParsingTable, SYNC_TOKENS, build_default_table
from .tokens import Token, TokenType


@dataclass
class ParseNode:
    symbol: str
    token: Token | None = None
    children: list["ParseNode"] = field(default_factory=list)


@dataclass
class LL1Parser:
    table: PredictiveParsingTable = field(default_factory=build_default_table)
    diagnostics: list[Diagnostic] = field(default_factory=list)

    def parse(self, tokens: list[Token]) -> ProgramNode:
        self.diagnostics.clear()
        filtered_tokens = [token for token in tokens if token.token_type is not TokenType.NEWLINE]
        if not filtered_tokens or filtered_tokens[-1].token_type is not TokenType.EOF:
            filtered_tokens.append(
                Token(TokenType.EOF, "", tokens[-1].line if tokens else 1, tokens[-1].column if tokens else 1)
            )

        root = ParseNode(START_SYMBOL)
        stack: list[tuple[str, ParseNode]] = [
            (ENDMARKER, ParseNode(ENDMARKER)),
            (START_SYMBOL, root),
        ]
        index = 0

        while stack:
            top_symbol, top_node = stack.pop()
            current_token = filtered_tokens[min(index, len(filtered_tokens) - 1)]
            lookahead = current_token.token_type.name

            if top_symbol in TERMINALS:
                if top_symbol == lookahead:
                    top_node.token = current_token
                    index += 1
                    continue

                self.diagnostics.append(
                    Diagnostic(
                        message=f"Expected {top_symbol}, found {lookahead}.",
                        line=current_token.line,
                        column=current_token.column,
                    )
                )
                recovered_index = self._recover_terminal(filtered_tokens, index, top_symbol)
                if recovered_index is not None:
                    index = recovered_index
                    current_token = filtered_tokens[min(index, len(filtered_tokens) - 1)]
                    if current_token.token_type.name == top_symbol:
                        top_node.token = current_token
                        index += 1
                continue

            production = self.table.get(top_symbol, lookahead)
            if production is None:
                self.diagnostics.append(
                    Diagnostic(
                        message=f"Unexpected token '{current_token.lexeme or lookahead}' while parsing {top_symbol}.",
                        line=current_token.line,
                        column=current_token.column,
                    )
                )
                index = self._recover_non_terminal(filtered_tokens, index, top_symbol)
                production = self.table.get(top_symbol, filtered_tokens[min(index, len(filtered_tokens) - 1)].token_type.name)
                if production is None:
                    continue

            if production == [EPSILON]:
                continue

            child_nodes = [ParseNode(symbol) for symbol in production]
            top_node.children = child_nodes

            for child in reversed(child_nodes):
                stack.append((child.symbol, child))

        return self._build_program(root)

    def _recover_terminal(
        self,
        tokens: list[Token],
        index: int,
        expected_terminal: str,
    ) -> int | None:
        current_index = index
        while current_index < len(tokens):
            lookahead = tokens[current_index].token_type.name
            if lookahead == expected_terminal:
                return current_index
            if lookahead in SYNC_TOKENS:
                return None
            current_index += 1
        return None

    def _recover_non_terminal(
        self,
        tokens: list[Token],
        index: int,
        non_terminal: str,
    ) -> int:
        current_index = index
        while current_index < len(tokens):
            lookahead = tokens[current_index].token_type.name
            if self.table.get(non_terminal, lookahead) is not None:
                return current_index
            if lookahead in SYNC_TOKENS:
                return current_index
            current_index += 1
        return min(current_index, len(tokens) - 1)

    def _build_program(self, root: ParseNode) -> Program:
        declarations: list[Any] = []
        automations: list[Automation] = []

        top_level_list = self._find_child(root, "top_level_list")
        if top_level_list is not None:
            self._collect_top_level_items(top_level_list, declarations, automations)

        return Program(declarations=declarations, automations=automations)

    def _collect_top_level_items(
        self,
        node: ParseNode,
        declarations: list[Any],
        automations: list[Automation],
    ) -> None:
        if not node.children:
            return

        item = self._build_top_level_item(node.children[0])
        if isinstance(item, Automation):
            automations.append(item)
        elif item is not None:
            declarations.append(item)

        self._collect_top_level_items(node.children[1], declarations, automations)

    def _build_top_level_item(self, node: ParseNode) -> EntityDeclaration | DeviceDeclaration | Automation | None:
        if not node.children:
            return None

        child = node.children[0]
        if child.symbol == "entity_decl":
            return self._build_entity_decl(child)
        if child.symbol == "device_decl":
            return self._build_device_decl(child)
        if child.symbol == "automation_decl":
            return self._build_automation(child)
        return None

    def _build_entity_decl(self, node: ParseNode) -> EntityDeclaration | None:
        name = self._token_lexeme(node, "IDENTIFIER")
        entity_id = self._token_lexeme(node, "DOTTED_ID")
        if name is None or entity_id is None:
            return None
        return EntityDeclaration(name=name, entity_id=entity_id)

    def _build_device_decl(self, node: ParseNode) -> DeviceDeclaration | None:
        name = self._token_lexeme(node, "IDENTIFIER", occurrence=0)
        domain = self._token_lexeme(node, "IDENTIFIER", occurrence=1)
        device_id = self._string_token_value(node, "STRING", occurrence=0)
        entity_id = self._string_token_value(node, "STRING", occurrence=1)
        if None in {name, domain, device_id, entity_id}:
            return None
        return DeviceDeclaration(name=name, domain=domain, device_id=device_id, entity_id=entity_id)

    def _build_automation(self, node: ParseNode) -> Automation | None:
        alias = self._string_token_value(node, "STRING")
        mode_node = self._find_child(node, "mode")
        block_node = self._find_child(node, "automation_block")
        if alias is None or mode_node is None or block_node is None:
            return None

        mode = self._first_terminal_lexeme(mode_node)
        description, triggers, conditions, actions = self._build_automation_block(block_node)
        return Automation(
            alias=alias,
            description=description or "",
            mode=mode or "single",
            triggers=triggers,
            conditions=conditions,
            actions=actions,
        )

    def _build_automation_block(
        self,
        node: ParseNode,
    ) -> tuple[str | None, list[Any], list[Condition], list[Action]]:
        description = self._build_description_opt(self._find_child(node, "description_section_opt"))
        triggers = self._build_triggers_opt(self._find_child(node, "triggers_section_opt"))
        conditions = self._build_conditions_opt(self._find_child(node, "conditions_section_opt"))
        actions = self._build_actions_opt(self._find_child(node, "actions_section_opt"))
        return description, triggers, conditions, actions

    def _build_description_opt(self, node: ParseNode | None) -> str | None:
        if node is None or not node.children:
            return None
        return self._string_token_value(node.children[0], "STRING")

    def _build_triggers_opt(self, node: ParseNode | None) -> list[Any]:
        if node is None or not node.children:
            return []
        return self._build_trigger_list_opt(self._find_child(node.children[0], "trigger_list_opt"))

    def _build_trigger_list_opt(self, node: ParseNode | None) -> list[Any]:
        if node is None or not node.children:
            return []
        current = self._build_trigger_stmt(node.children[0])
        rest = self._build_trigger_list_opt(node.children[1])
        return ([current] if current is not None else []) + rest

    def _build_trigger_stmt(self, node: ParseNode) -> Any | None:
        trigger_core = self._find_child(node, "trigger_core")
        if trigger_core is None or not trigger_core.children:
            return None
        child = trigger_core.children[0]
        if child.symbol == "ESTADO":
            return self._build_state_trigger(self._find_child(trigger_core, "state_trigger_core"))
        if child.symbol == "DISPOSITIVO":
            return self._build_device_trigger(self._find_child(trigger_core, "device_trigger_core"))
        if child.symbol == "SOL":
            return self._build_sun_trigger(self._find_child(trigger_core, "sun_trigger_core"))
        if child.symbol == "HORA":
            return self._build_time_trigger(self._find_child(trigger_core, "time_trigger_core"))
        return None

    def _build_state_trigger(self, node: ParseNode | None) -> StateTrigger | None:
        if node is None:
            return None
        entity_ids = self._build_entity_selector(self._find_child(node, "entity_selector"))
        from_states = self._build_optional_basic_values(self._find_child(node, "state_from_opt"))
        to_states = self._build_basic_values(self._find_child(node, "basic_or_list_value"))
        alias = self._build_optional_string(self._find_child(node, "trigger_alias_opt"))
        trigger_id = self._build_optional_string(self._find_child(node, "trigger_id_opt"))
        duration = self._build_optional_duration(self._find_child(node, "trigger_for_opt"))
        if not entity_ids or not to_states:
            return None
        return StateTrigger(
            entity_ids=entity_ids,
            to_states=to_states,
            from_states=from_states,
            trigger_id=trigger_id,
            alias=alias,
            for_duration=duration,
        )

    def _build_device_trigger(self, node: ParseNode | None) -> DeviceTrigger | None:
        if node is None:
            return None
        domain, device_id, entity_id = self._build_device_subject(self._find_child(node, "device_subject"))
        mode_info = self._build_device_mode(self._find_child(node, "device_mode"))
        trigger_id = self._build_optional_string(self._find_child(node, "trigger_id_opt"))
        duration = self._build_optional_duration(self._find_child(node, "trigger_for_opt"))
        if domain is None or mode_info is None:
            return None
        return DeviceTrigger(
            domain=domain,
            device_id=device_id or "",
            entity_id=entity_id or "",
            device_type=mode_info["device_type"],
            trigger_id=trigger_id,
            above=mode_info.get("above"),
            below=mode_info.get("below"),
            for_duration=duration,
        )

    def _build_sun_trigger(self, node: ParseNode | None) -> SunTrigger | None:
        if node is None:
            return None
        event = self._build_sun_event(self._find_child(node, "sun_event"))
        offset = self._build_optional_string(self._find_child(node, "sun_offset_opt"))
        trigger_id = self._build_optional_string(self._find_child(node, "trigger_id_opt"))
        if event is None:
            return None
        return SunTrigger(event=event, offset=offset, trigger_id=trigger_id)

    def _build_time_trigger(self, node: ParseNode | None) -> TimeTrigger | None:
        if node is None:
            return None
        at = self._string_token_value(node, "STRING")
        trigger_id = self._build_optional_string(self._find_child(node, "trigger_id_opt"))
        weekdays = self._build_weekday_opt(self._find_child(node, "weekday_opt"))
        if at is None:
            return None
        return TimeTrigger(at=at, trigger_id=trigger_id, weekdays=weekdays)

    def _build_conditions_opt(self, node: ParseNode | None) -> list[Condition]:
        if node is None or not node.children:
            return []
        return self._build_condition_list_opt(self._find_child(node.children[0], "condition_list_opt"))

    def _build_condition_list_opt(self, node: ParseNode | None) -> list[Condition]:
        if node is None or not node.children:
            return []
        current = self._build_condition_stmt(node.children[0])
        rest = self._build_condition_list_opt(node.children[1])
        return ([current] if current is not None else []) + rest

    def _build_condition_stmt(self, node: ParseNode) -> Condition | None:
        condition = self._build_condition_clause(self._find_child(node, "condition_clause"))
        enabled = self._build_optional_boolean(self._find_child(node, "condition_enabled_opt"))
        self._apply_condition_enabled(condition, enabled)
        return condition

    def _build_condition_entries(self, node: ParseNode | None) -> list[Condition]:
        if node is None or not node.children:
            return []
        current = self._build_condition_entry(node.children[0])
        rest = self._build_condition_entries(node.children[1])
        return ([current] if current is not None else []) + rest

    def _build_condition_entry(self, node: ParseNode) -> Condition | None:
        condition = self._build_condition_clause(self._find_child(node, "condition_clause"))
        enabled = self._build_optional_boolean(self._find_child(node, "condition_enabled_opt"))
        self._apply_condition_enabled(condition, enabled)
        return condition

    def _build_condition_clause(self, node: ParseNode | None) -> Condition | None:
        if node is None or not node.children:
            return None
        child = node.children[0]
        if child.symbol == "simple_condition":
            return self._build_simple_condition(child)
        if child.symbol == "logical_condition":
            return self._build_logical_condition(child)
        return None

    def _build_simple_condition(self, node: ParseNode) -> Condition | None:
        if not node.children:
            return None
        child = node.children[0]
        if child.symbol == "state_condition":
            return self._build_state_condition(child)
        if child.symbol == "device_condition":
            return self._build_device_condition(child)
        if child.symbol == "trigger_condition":
            return self._build_trigger_condition(child)
        if child.symbol == "time_condition":
            return self._build_time_condition(child)
        if child.symbol == "sun_condition":
            return self._build_sun_condition(child)
        return None

    def _build_logical_condition(self, node: ParseNode) -> LogicalCondition | None:
        if not node.children:
            return None
        operator_symbol = node.children[0].symbol
        operator = "or" if operator_symbol == "QUALQUER" else "and"
        conditions = self._build_condition_entries(self._find_child(node, "condition_entry_list_opt"))
        return LogicalCondition(operator=operator, conditions=conditions)

    def _build_state_condition(self, node: ParseNode) -> StateCondition | None:
        entity_id = self._build_entity_ref(self._find_child(node, "entity_ref"))
        states = self._build_basic_values(self._find_child(node, "basic_or_list_value"))
        if entity_id is None or not states:
            return None
        return StateCondition(entity_id=entity_id, states=states)

    def _build_device_condition(self, node: ParseNode) -> DeviceCondition | None:
        domain, device_id, entity_id = self._build_device_subject(self._find_child(node, "device_subject"))
        mode_info = self._build_device_mode(self._find_child(node, "device_condition_mode"))
        if domain is None or mode_info is None:
            return None
        return DeviceCondition(
            domain=domain,
            device_id=device_id or "",
            entity_id=entity_id or "",
            condition_type=mode_info["condition_type"],
        )

    def _build_trigger_condition(self, node: ParseNode) -> TriggerCondition | None:
        ids = self._build_trigger_id_selector(self._find_child(node, "trigger_id_selector"))
        if not ids:
            return None
        return TriggerCondition(ids=ids)

    def _build_time_condition(self, node: ParseNode) -> TimeCondition | None:
        mode_node = self._find_child(node, "time_condition_mode")
        if mode_node is None or not mode_node.children:
            return None

        first = mode_node.children[0].symbol
        if first == "ENTRE":
            after = self._string_token_value(mode_node, "STRING", occurrence=0)
            before = self._string_token_value(mode_node, "STRING", occurrence=1)
            return TimeCondition(after=after, before=before)
        if first == "DEPOIS":
            after = self._string_token_value(mode_node, "STRING", occurrence=0)
            before = self._build_optional_string(self._find_child(mode_node, "time_before_opt"))
            return TimeCondition(after=after, before=before)
        if first == "ANTES":
            before = self._string_token_value(mode_node, "STRING", occurrence=0)
            after = self._build_optional_string(self._find_child(mode_node, "time_after_opt"))
            return TimeCondition(after=after, before=before)
        return None

    def _build_sun_condition(self, node: ParseNode) -> SunCondition | None:
        mode_node = self._find_child(node, "sun_condition_mode")
        if mode_node is None or not mode_node.children:
            return None
        first = mode_node.children[0].symbol
        if first == "ANTES":
            before = self._build_sun_event(self._find_child(mode_node, "sun_event"))
            after = self._build_sun_event(
                self._find_child(self._find_child(mode_node, "sun_after_opt") or ParseNode("empty"), "sun_event")
            )
            return SunCondition(before=before, after=after)
        if first == "DEPOIS":
            after = self._build_sun_event(self._find_child(mode_node, "sun_event"))
            before = self._build_sun_event(
                self._find_child(self._find_child(mode_node, "sun_before_opt") or ParseNode("empty"), "sun_event")
            )
            return SunCondition(before=before, after=after)
        return None

    def _build_actions_opt(self, node: ParseNode | None) -> list[Action]:
        if node is None or not node.children:
            return []
        return self._build_action_list_opt(self._find_child(node.children[0], "action_list_opt"))

    def _build_action_list_opt(self, node: ParseNode | None) -> list[Action]:
        if node is None or not node.children:
            return []
        current = self._build_action_stmt(node.children[0])
        rest = self._build_action_list_opt(node.children[1])
        return ([current] if current is not None else []) + rest

    def _build_action_stmt(self, node: ParseNode) -> Action | None:
        if not node.children:
            return None
        child = node.children[0]
        if child.symbol == "simple_action_stmt":
            return self._build_simple_action(child)
        if child.symbol == "block_action_stmt":
            return self._build_block_action(child)
        return None

    def _build_simple_action(self, node: ParseNode) -> Action | None:
        if not node.children:
            return None
        if node.children[0].symbol == "FACA":
            action = self._build_action_command(self._find_child(node, "action_command"))
            enabled = self._build_optional_boolean(self._find_child(node, "action_enabled_opt"))
            if isinstance(action, (DeviceAction, ServiceAction)):
                action.enabled = enabled
            return action

        duration = self._build_duration(self._find_child(node, "duration_value"))
        if duration is None:
            return None
        return DelayAction(duration=duration)

    def _build_block_action(self, node: ParseNode) -> Action | None:
        if not node.children:
            return None
        enabled = self._build_optional_boolean(self._find_child(node, "action_enabled_opt"))
        child = node.children[0]
        action: Action | None
        if child.symbol == "action_if_stmt":
            action = self._build_if_action(child)
        else:
            action = self._build_choose_action(child)

        if isinstance(action, (DeviceAction, ServiceAction)):
            action.enabled = enabled
        return action

    def _build_action_command(self, node: ParseNode | None) -> Action | None:
        if node is None or not node.children:
            return None
        child = node.children[0]
        if child.symbol == "device_action":
            return self._build_device_action(child)
        if child.symbol == "service_action":
            return self._build_service_action(child)
        return None

    def _build_device_action(self, node: ParseNode) -> DeviceAction | None:
        action_type = self._first_terminal_lexeme(self._find_child(node, "device_verb"))
        domain, device_id, entity_id = self._build_device_subject(self._find_child(node, "device_subject"))
        if action_type is None or domain is None:
            return None
        return DeviceAction(
            domain=domain,
            device_id=device_id or "",
            entity_id=entity_id or "",
            action_type=action_type,
        )

    def _build_service_action(self, node: ParseNode) -> ServiceAction | None:
        service = self._token_lexeme(node, "DOTTED_ID")
        if service is None:
            return None
        target_entity_ids, target_device_ids = self._build_service_targets(self._find_child(node, "service_target_opt"))
        data = self._build_optional_map(self._find_child(node, "service_data_opt"))
        metadata = self._build_optional_map(self._find_child(node, "service_metadata_opt"))
        return ServiceAction(
            service=service,
            target_entity_ids=target_entity_ids,
            target_device_ids=target_device_ids,
            data=data,
            metadata=metadata,
        )

    def _build_if_action(self, node: ParseNode) -> IfAction | None:
        condition = self._build_condition_clause(self._find_child(node, "condition_clause"))
        then_actions = self._build_action_block(self._find_child(node, "action_block"))
        else_actions = self._build_else_actions(self._find_child(node, "action_else_opt"))
        if condition is None:
            return None
        return IfAction(conditions=[condition], then_actions=then_actions, else_actions=else_actions)

    def _build_else_actions(self, node: ParseNode | None) -> list[Action]:
        if node is None or not node.children:
            return []
        return self._build_action_block(self._find_child(node, "action_block"))

    def _build_action_block(self, node: ParseNode | None) -> list[Action]:
        if node is None:
            return []
        return self._build_action_list_opt(self._find_child(node, "action_list_opt"))

    def _build_choose_action(self, node: ParseNode) -> ChooseAction | None:
        cases = self._build_case_list_opt(self._find_child(node, "case_list_opt"))
        return ChooseAction(cases=cases)

    def _build_case_list_opt(self, node: ParseNode | None) -> list[ChooseCase]:
        if node is None or not node.children:
            return []
        current = self._build_case_item(node.children[0])
        rest = self._build_case_list_opt(node.children[1])
        return ([current] if current is not None else []) + rest

    def _build_case_item(self, node: ParseNode) -> ChooseCase | None:
        condition = self._build_condition_clause(self._find_child(node, "condition_clause"))
        sequence = self._build_action_block(self._find_child(node, "action_block"))
        if condition is None:
            return None
        return ChooseCase(conditions=[condition], sequence=sequence)

    def _build_service_targets(self, node: ParseNode | None) -> tuple[list[str], list[str]]:
        if node is None or not node.children:
            return [], []
        target_block = self._find_child(node, "target_block")
        if target_block is None:
            return [], []
        return self._build_target_entries(self._find_child(target_block, "target_entry_list_opt"))

    def _build_target_entries(self, node: ParseNode | None) -> tuple[list[str], list[str]]:
        if node is None or not node.children:
            return [], []
        entity_ids: list[str] = []
        device_ids: list[str] = []
        self._collect_target_entries(node, entity_ids, device_ids)
        return entity_ids, device_ids

    def _collect_target_entries(self, node: ParseNode, entity_ids: list[str], device_ids: list[str]) -> None:
        if not node.children:
            return
        entry = node.children[0]
        kind = entry.children[0].symbol if entry.children else None
        if kind == "ENTITY_ID":
            entity_ids.extend(self._build_target_entity_value(self._find_child(entry, "target_entity_value")))
        elif kind == "DEVICE_ID":
            device_ids.extend(self._build_target_device_value(self._find_child(entry, "target_device_value")))
        self._collect_target_entries(node.children[1], entity_ids, device_ids)

    def _build_target_entity_value(self, node: ParseNode | None) -> list[str]:
        if node is None or not node.children:
            return []
        child = node.children[0]
        if child.symbol == "entity_ref":
            value = self._build_entity_ref(child)
            return [value] if value is not None else []
        return self._build_entity_list(child)

    def _build_target_device_value(self, node: ParseNode | None) -> list[str]:
        if node is None or not node.children:
            return []
        child = node.children[0]
        if child.symbol == "STRING":
            value = self._string_token_value(node, "STRING")
            return [value] if value is not None else []
        return [str(item.value) for item in self._build_basic_list(child)]

    def _build_optional_map(self, node: ParseNode | None) -> dict[str, Any]:
        if node is None or not node.children:
            return {}
        map_node = self._find_child(node, "map_literal")
        if map_node is None:
            return {}
        return self._build_map_literal(map_node)

    def _build_map_literal(self, node: ParseNode | None) -> dict[str, Any]:
        if node is None:
            return {}
        return self._build_data_entries(self._find_child(node, "data_entry_list_opt"))

    def _build_data_entries(self, node: ParseNode | None) -> dict[str, Any]:
        if node is None or not node.children:
            return {}
        result: dict[str, Any] = {}
        self._collect_data_entries(node, result)
        return result

    def _collect_data_entries(self, node: ParseNode, result: dict[str, Any]) -> None:
        if not node.children:
            return
        entry = node.children[0]
        key = self._build_map_key(self._find_child(entry, "map_key"))
        value = self._build_value(self._find_child(entry, "value"))
        if key is not None:
            result[key] = value
        self._collect_data_entries(node.children[1], result)

    def _build_map_key(self, node: ParseNode | None) -> str | None:
        if node is None or not node.children:
            return None
        token = self._find_first_token(node)
        if token is None:
            return None
        return token.lexeme

    def _build_value(self, node: ParseNode | None) -> Any:
        if node is None or not node.children:
            return None
        child = node.children[0]
        if child.symbol == "atomic_value":
            return self._build_atomic_value(child)
        if child.symbol == "list_value":
            return self._build_list_value(child)
        if child.symbol == "map_literal":
            return self._build_map_literal(child)
        return None

    def _build_atomic_value(self, node: ParseNode) -> Any:
        child = node.children[0]
        if child.symbol == "basic_value":
            literal = self._build_basic_value(child)
            return literal.value if literal is not None else None
        duration = self._build_duration(child)
        return duration.raw if duration is not None else None

    def _build_list_value(self, node: ParseNode) -> list[Any]:
        if not node.children:
            return []
        values = [self._build_value(node.children[1])]
        self._collect_list_tail(node.children[2], values)
        return values

    def _collect_list_tail(self, node: ParseNode, values: list[Any]) -> None:
        if not node.children:
            return
        values.append(self._build_value(node.children[1]))
        self._collect_list_tail(node.children[2], values)

    def _build_basic_values(self, node: ParseNode | None) -> list[LiteralValue]:
        if node is None or not node.children:
            return []
        child = node.children[0]
        if child.symbol == "basic_value":
            literal = self._build_basic_value(child)
            return [literal] if literal is not None else []
        return self._build_basic_list(child)

    def _build_optional_basic_values(self, node: ParseNode | None) -> list[LiteralValue] | None:
        if node is None or not node.children:
            return None
        return self._build_basic_values(node.children[1])

    def _build_basic_list(self, node: ParseNode) -> list[LiteralValue]:
        if not node.children:
            return []
        values = []
        first_value = self._build_basic_value(node.children[1])
        if first_value is not None:
            values.append(first_value)
        self._collect_basic_list_tail(node.children[2], values)
        return values

    def _collect_basic_list_tail(self, node: ParseNode, values: list[LiteralValue]) -> None:
        if not node.children:
            return
        literal = self._build_basic_value(node.children[1])
        if literal is not None:
            values.append(literal)
        self._collect_basic_list_tail(node.children[2], values)

    def _build_basic_value(self, node: ParseNode) -> LiteralValue | None:
        if not node.children:
            return None
        child = node.children[0]
        if child.symbol == "STRING":
            value = self._token_string_value(child.token)
        elif child.symbol == "NUMBER":
            value = self._token_number_value(child.token)
        elif child.symbol == "boolean_literal":
            value = self._build_boolean_literal(child)
        else:
            value = child.token.lexeme if child.token is not None else None
        if value is None:
            return None
        return LiteralValue(value=value)

    def _build_trigger_id_selector(self, node: ParseNode | None) -> list[str]:
        if node is None or not node.children:
            return []
        child = node.children[0]
        if child.symbol == "trigger_id_value":
            value = self._build_trigger_id_value(child)
            return [value] if value is not None else []
        return self._build_trigger_id_list(child)

    def _build_trigger_id_list(self, node: ParseNode) -> list[str]:
        values = []
        first_value = self._build_trigger_id_value(node.children[1])
        if first_value is not None:
            values.append(first_value)
        self._collect_trigger_id_tail(node.children[2], values)
        return values

    def _collect_trigger_id_tail(self, node: ParseNode, values: list[str]) -> None:
        if not node.children:
            return
        value = self._build_trigger_id_value(node.children[1])
        if value is not None:
            values.append(value)
        self._collect_trigger_id_tail(node.children[2], values)

    def _build_trigger_id_value(self, node: ParseNode) -> str | None:
        child = node.children[0]
        if child.symbol == "STRING":
            return self._token_string_value(child.token)
        if child.token is not None:
            return child.token.lexeme
        return None

    def _build_entity_selector(self, node: ParseNode | None) -> list[str]:
        if node is None or not node.children:
            return []
        child = node.children[0]
        if child.symbol == "entity_ref":
            value = self._build_entity_ref(child)
            return [value] if value is not None else []
        return self._build_entity_list(child)

    def _build_entity_list(self, node: ParseNode) -> list[str]:
        values = []
        first_value = self._build_entity_ref(node.children[1])
        if first_value is not None:
            values.append(first_value)
        self._collect_entity_list_tail(node.children[2], values)
        return values

    def _collect_entity_list_tail(self, node: ParseNode, values: list[str]) -> None:
        if not node.children:
            return
        value = self._build_entity_ref(node.children[1])
        if value is not None:
            values.append(value)
        self._collect_entity_list_tail(node.children[2], values)

    def _build_entity_ref(self, node: ParseNode | None) -> str | None:
        if node is None or not node.children:
            return None
        child = node.children[0]
        return child.token.lexeme if child.token is not None else None

    def _build_device_subject(self, node: ParseNode | None) -> tuple[str | None, str | None, str | None]:
        if node is None or not node.children:
            return None, None, None
        domain = node.children[0].token.lexeme if node.children[0].token is not None else None
        tail = self._find_child(node, "device_subject_tail")
        if tail is None or not tail.children:
            return domain, None, None
        device_id = self._string_token_value(tail, "STRING", occurrence=0)
        entity_id = self._string_token_value(tail, "STRING", occurrence=1)
        return domain, device_id, entity_id

    def _build_device_mode(self, node: ParseNode | None) -> dict[str, Any] | None:
        if node is None or not node.children:
            return None
        first_symbol = node.children[0].symbol
        if first_symbol in {
            "LIGADO",
            "DESLIGADO",
            "MOVIMENTO",
            "ABERTO",
            "FECHADO",
            "ABERTA",
            "FECHADA",
            "ARMADO",
            "DESARMADO",
        }:
            lexeme = node.children[0].token.lexeme if node.children[0].token is not None else None
            if lexeme is None:
                return None
            return {"device_type": lexeme, "condition_type": lexeme}

        metric = self._first_terminal_lexeme(self._find_child(node, "metric_name"))
        comparison = self._first_terminal_lexeme(self._find_child(node, "comparison_op"))
        value = self._build_basic_value(self._find_child(node, "basic_value"))
        if metric is None or comparison is None or value is None:
            return None

        result = {
            "device_type": metric,
            "condition_type": f"{metric}_{comparison}",
        }
        if comparison == "acima":
            result["above"] = value
        elif comparison == "abaixo":
            result["below"] = value
        return result

    def _build_sun_event(self, node: ParseNode | None) -> str | None:
        if node is None or not node.children:
            return None
        first = node.children[0].symbol
        if first == "POR_DO_SOL":
            return "sunset"
        if first == "NASCER_DO_SOL":
            return "sunrise"
        return None

    def _build_optional_duration(self, node: ParseNode | None) -> Duration | None:
        if node is None or not node.children:
            return None
        return self._build_duration(self._find_child(node, "duration_value"))

    def _build_weekday_opt(self, node: ParseNode | None) -> list[str] | None:
        if node is None or not node.children:
            return None
        weekday_list = self._find_child(node, "weekday_list")
        if weekday_list is None or not weekday_list.children:
            return None
        weekdays = [self._token_lexeme(weekday_list.children[1], "IDENTIFIER")]
        self._collect_weekday_tail(weekday_list.children[2], weekdays)
        return [day for day in weekdays if day is not None]

    def _collect_weekday_tail(self, node: ParseNode, weekdays: list[str | None]) -> None:
        if not node.children:
            return
        weekdays.append(self._token_lexeme(node.children[1], "IDENTIFIER"))
        self._collect_weekday_tail(node.children[2], weekdays)

    def _build_duration(self, node: ParseNode | None) -> Duration | None:
        if node is None or not node.children:
            return None
        token = self._find_first_token(node)
        if token is None:
            return None
        return Duration(raw=token.lexeme)

    def _build_optional_string(self, node: ParseNode | None) -> str | None:
        if node is None or not node.children:
            return None
        return self._string_token_value(node, "STRING")

    def _build_optional_boolean(self, node: ParseNode | None) -> bool | None:
        if node is None or not node.children:
            return None
        boolean_node = self._find_child(node, "boolean_literal")
        return self._build_boolean_literal(boolean_node)

    @staticmethod
    def _apply_condition_enabled(condition: Condition | None, enabled: bool | None) -> None:
        if condition is None:
            return
        if hasattr(condition, "enabled"):
            condition.enabled = enabled

    def _build_boolean_literal(self, node: ParseNode | None) -> bool | None:
        if node is None or not node.children:
            return None
        symbol = node.children[0].symbol
        if symbol == "TRUE":
            return True
        if symbol == "FALSE":
            return False
        return None

    def _find_child(self, node: ParseNode, symbol: str) -> ParseNode | None:
        for child in node.children:
            if child.symbol == symbol:
                return child
        return None

    def _find_first_token(self, node: ParseNode | None) -> Token | None:
        if node is None:
            return None
        if node.token is not None:
            return node.token
        for child in node.children:
            token = self._find_first_token(child)
            if token is not None:
                return token
        return None

    def _token_lexeme(self, node: ParseNode, symbol: str, occurrence: int = 0) -> str | None:
        count = 0
        for child in self._iter_nodes(node):
            if child.symbol == symbol and child.token is not None:
                if count == occurrence:
                    return child.token.lexeme
                count += 1
        return None

    def _string_token_value(self, node: ParseNode, symbol: str, occurrence: int = 0) -> str | None:
        lexeme = self._token_lexeme(node, symbol, occurrence)
        return self._unquote_string(lexeme) if lexeme is not None else None

    def _first_terminal_lexeme(self, node: ParseNode | None) -> str | None:
        token = self._find_first_token(node)
        if token is None:
            return None
        return token.lexeme

    def _iter_nodes(self, node: ParseNode) -> list[ParseNode]:
        result = [node]
        for child in node.children:
            result.extend(self._iter_nodes(child))
        return result

    @staticmethod
    def _unquote_string(lexeme: str) -> str:
        inner = lexeme[1:-1]
        return inner.replace('\\"', '"').replace("\\\\", "\\")

    @staticmethod
    def _token_string_value(token: Token | None) -> str | None:
        if token is None:
            return None
        inner = token.lexeme[1:-1]
        return inner.replace('\\"', '"').replace("\\\\", "\\")

    @staticmethod
    def _token_number_value(token: Token | None) -> int | float | None:
        if token is None:
            return None
        if "." in token.lexeme:
            return float(token.lexeme)
        return int(token.lexeme)
