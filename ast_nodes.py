from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Nó raiz
# ---------------------------------------------------------------------------

@dataclass
class ProgramNode:
    """Raiz da AST — lista de automações."""
    automations: list[AutomationNode]

    def __repr__(self):
        return f"Program({len(self.automations)} automações)"


# ---------------------------------------------------------------------------
# Automação
# ---------------------------------------------------------------------------

@dataclass
class AutomationNode:
    """Representa um bloco `automacao "Nome" { ... }`."""
    name: str
    triggers: list[TriggerNode]
    conditions: list[ConditionNode]
    actions: list[ActionNode]
    mode: str = 'single'        # single | restart | queued | parallel
    line: int = 0               # linha do source para mensagens de erro

    def __repr__(self):
        return f'Automation("{self.name}", triggers={len(self.triggers)}, mode={self.mode})'


# ---------------------------------------------------------------------------
# Triggers
# ---------------------------------------------------------------------------

@dataclass
class TriggerNode:
    """
    Tipos de trigger:
      - 'state'   → sensor/luz/interruptor muda_para <valor>
      - 'time'    → ao_horario HH:MM
      - 'sun'     → nascer_do_sol / por_do_sol (com offset opcional)
      - 'timer'   → timer.<entity> muda_para idle/active
    """
    kind: str
    entity: Optional[str] = None
    to: Optional[str] = None
    at: Optional[str] = None        # para kind='time'
    sun_event: Optional[str] = None # 'sunrise' ou 'sunset'
    offset: Optional[str] = None    # ex: '-01:30:00'
    trigger_id: Optional[str] = None
    line: int = 0

    def __repr__(self):
        if self.kind == 'state':
            return f'Trigger(state, {self.entity} → {self.to})'
        if self.kind == 'time':
            return f'Trigger(time, at={self.at})'
        if self.kind == 'sun':
            return f'Trigger(sun, {self.sun_event}, offset={self.offset})'
        if self.kind == 'timer':
            return f'Trigger(timer, {self.entity} → {self.to})'
        return f'Trigger({self.kind})'


# ---------------------------------------------------------------------------
# Condições
# ---------------------------------------------------------------------------

@dataclass
class ConditionNode:
    """
    Tipos de condição:
      - 'state'   → <entity_id> esta <valor>
      - 'time'    → horario entre HH:MM e HH:MM
      - 'trigger' → (interno — referencia trigger_id no choose/if)
    """
    kind: str
    entity: Optional[str] = None
    state: Optional[str] = None
    after: Optional[str] = None     # para kind='time'
    before: Optional[str] = None    # para kind='time'
    trigger_id: Optional[str] = None
    line: int = 0

    def __repr__(self):
        if self.kind == 'state':
            return f'Condition(state, {self.entity} is {self.state})'
        if self.kind == 'time':
            return f'Condition(time, {self.after}–{self.before})'
        return f'Condition({self.kind})'


# ---------------------------------------------------------------------------
# Ações
# ---------------------------------------------------------------------------

@dataclass
class ActionNode:
    """
    Tipos de ação:
      - 'ligar'     → ligar <entity_id> (brilho N%)?
      - 'desligar'  → desligar <entity_id>
      - 'aguardar'  → aguardar <duracao>
      - 'notificar' → notificar "mensagem" para <notify.entity>
      - 'if'        → se <conditions> entao: <actions> (senao: <actions>)? fim
      - 'escolher'  → escolher: <choices> fim
    """
    kind: str
    entity: Optional[str] = None
    duration: Optional[str] = None          # ex: '45s', '4min', '1h'
    message: Optional[str] = None
    notify_target: Optional[str] = None
    brightness: Optional[int] = None        # 0-100 (%)
    then_actions: list[ActionNode] = field(default_factory=list)
    else_actions: list[ActionNode] = field(default_factory=list)
    conditions: list[ConditionNode] = field(default_factory=list)
    choices: list[ChoiceNode] = field(default_factory=list)
    line: int = 0

    def __repr__(self):
        if self.kind == 'ligar':
            b = f' brilho={self.brightness}%' if self.brightness else ''
            return f'Action(ligar, {self.entity}{b})'
        if self.kind == 'desligar':
            return f'Action(desligar, {self.entity})'
        if self.kind == 'aguardar':
            return f'Action(aguardar, {self.duration})'
        if self.kind == 'notificar':
            return f'Action(notificar, "{self.message}" → {self.notify_target})'
        if self.kind == 'if':
            has_else = ' [com senão]' if self.else_actions else ''
            return f'Action(if, {len(self.conditions)} cond, {len(self.then_actions)} então{has_else})'
        if self.kind == 'escolher':
            return f'Action(escolher, {len(self.choices)} casos)'
        return f'Action({self.kind})'


@dataclass
class ChoiceNode:
    """Um `caso` dentro de um bloco `escolher`."""
    conditions: list[ConditionNode]
    actions: list[ActionNode]
    line: int = 0

    def __repr__(self):
        return f'Choice({len(self.conditions)} cond → {len(self.actions)} ações)'


# ---------------------------------------------------------------------------
# Utilitários de travessia
# ---------------------------------------------------------------------------

def walk(node, visitor):
    """
    Percorre a AST em pré-ordem chamando visitor(node).
    Útil para o analisador semântico e o gerador de código.
    """
    visitor(node)

    if isinstance(node, ProgramNode):
        for auto in node.automations:
            walk(auto, visitor)

    elif isinstance(node, AutomationNode):
        for t in node.triggers:
            walk(t, visitor)
        for c in node.conditions:
            walk(c, visitor)
        for a in node.actions:
            walk(a, visitor)

    elif isinstance(node, ActionNode):
        for c in node.conditions:
            walk(c, visitor)
        for a in node.then_actions:
            walk(a, visitor)
        for a in node.else_actions:
            walk(a, visitor)
        for ch in node.choices:
            walk(ch, visitor)

    elif isinstance(node, ChoiceNode):
        for c in node.conditions:
            walk(c, visitor)
        for a in node.actions:
            walk(a, visitor)
