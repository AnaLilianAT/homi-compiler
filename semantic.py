"""
Analisador Semântico — Linguagem Homi

Responsabilidades:
  1. Verificar que o domínio de cada entity_id é reconhecido.
  2. Impedir estados incompatíveis com o domínio da entidade
     (ex: estado 'disarmed' em luz, 'on' em painel de alarme).
  3. Exigir que 'brilho' só seja usado com domínio 'light'.
  4. Exigir que o alvo de 'notificar' seja do domínio 'notify'.
  5. Impedir duração negativa em 'aguardar'.
  6. Emitir aviso para nomes de automação duplicados.
"""

from ast_nodes import (
    ProgramNode, AutomationNode,
    TriggerNode, ConditionNode,
    ActionNode, ChoiceNode,
)
from errors import ErroSemantico


# ---------------------------------------------------------------------------
# Tabela de Símbolos
# ---------------------------------------------------------------------------

class SymbolTable:
    """Mapeia domínios HA a tipos Homi e define estados válidos por tipo."""

    # Prefixo do entity_id → tipo semântico Homi
    DOMAIN_TYPES: dict[str, str] = {
        'light':              'luz',
        'switch':             'interruptor',
        'binary_sensor':      'sensor',
        'sensor':             'sensor',
        'alarm_control_panel':'alarme',
        'timer':              'timer',
        'media_player':       'media',
        'cover':              'cortina',
        'notify':             'notificacao',
        'automation':         'automacao',
        'input_boolean':      'interruptor',
        'input_number':       'sensor',
        'input_select':       'sensor',
        'input_text':         'sensor',
        'person':             'sensor',
        'zone':               'sensor',
        'weather':            'sensor',
        'climate':            'sensor',
        'vacuum':             'sensor',
        'fan':                'interruptor',
        'lock':               'sensor',
        'camera':             'sensor',
        'number':             'sensor',
        'button':             'sensor',
    }

    # Estados que pertencem EXCLUSIVAMENTE a domínios de alarme
    ALARM_ONLY_STATES: frozenset[str] = frozenset({
        'disarmed', 'armed_home', 'armed_away',
        'armed_night', 'armed_vacation', 'triggered',
    })

    # Domínios que aceitam apenas on/off como estados lógicos
    ON_OFF_DOMAINS: frozenset[str] = frozenset({
        'light', 'switch', 'binary_sensor', 'input_boolean',
        'fan', 'automation',
    })

    def domain(self, entity_id: str) -> str:
        return entity_id.split('.')[0]

    def entity_type(self, entity_id: str) -> str | None:
        return self.DOMAIN_TYPES.get(self.domain(entity_id))

    def is_known_domain(self, entity_id: str) -> bool:
        return self.domain(entity_id) in self.DOMAIN_TYPES


# ---------------------------------------------------------------------------
# Analisador Semântico
# ---------------------------------------------------------------------------

class SemanticAnalyzer:

    def __init__(self):
        self.table = SymbolTable()
        self.errors: list[ErroSemantico] = []
        self.warnings: list[str] = []
        self._seen_names: set[str] = set()

    # ------------------------------------------------------------------ API

    def analyze(self, program: ProgramNode) -> bool:
        """
        Percorre a AST aplicando todas as regras semânticas.
        Imprime erros e avisos; retorna True se não houver erros.
        """
        for auto in program.automations:
            self._check_automation(auto)

        for err in self.errors:
            print(err)
        for warn in self.warnings:
            print(f"Aviso semântico: {warn}")

        return len(self.errors) == 0

    # ---------------------------------------------------------- helpers internos

    def _error(self, msg: str, line: int = 0):
        self.errors.append(ErroSemantico(msg, line=line))

    def _warn(self, msg: str):
        self.warnings.append(msg)

    # ---------------------------------------------------------- automação

    def _check_automation(self, auto: AutomationNode):
        if auto.name in self._seen_names:
            self._warn(f"nome de automação duplicado: '{auto.name}'")
        self._seen_names.add(auto.name)

        for t in auto.triggers:
            self._check_trigger(t)
        for c in auto.conditions:
            self._check_condition(c)
        for a in auto.actions:
            self._check_action(a)

    # ---------------------------------------------------------- triggers

    def _check_trigger(self, t: TriggerNode):
        if not t.entity:
            return
        if not self.table.is_known_domain(t.entity):
            self._error(
                f"domínio desconhecido: '{self.table.domain(t.entity)}' "
                f"em '{t.entity}'",
                line=t.line,
            )

    # ---------------------------------------------------------- condições

    def _check_condition(self, c: ConditionNode):
        if c.kind != 'state' or not c.entity:
            return

        domain = self.table.domain(c.entity)

        if not self.table.is_known_domain(c.entity):
            self._error(
                f"domínio desconhecido: '{domain}' em '{c.entity}'",
                line=c.line,
            )
            return

        state = str(c.state) if c.state is not None else ''

        # Estado exclusivo de alarme usado em outro domínio
        if state in self.table.ALARM_ONLY_STATES and domain != 'alarm_control_panel':
            self._error(
                f"estado '{state}' é válido apenas para 'alarm_control_panel'; "
                f"'{c.entity}' tem domínio '{domain}'",
                line=c.line,
            )

        # Estado on/off em domínio que não o suporta logicamente
        # (apenas aviso — sensores podem ter qualquer estado)

    # ---------------------------------------------------------- ações

    def _check_action(self, a: ActionNode):

        if a.kind == 'ligar':
            self._check_entity_domain(a.entity, a.line)
            # 'brilho' é exclusivo do domínio light
            if a.brightness is not None:
                domain = self.table.domain(a.entity)
                if domain != 'light':
                    self._error(
                        f"'brilho' só pode ser usado com entidades do domínio 'light'; "
                        f"'{a.entity}' pertence ao domínio '{domain}'",
                        line=a.line,
                    )

        elif a.kind == 'desligar':
            self._check_entity_domain(a.entity, a.line)

        elif a.kind == 'notificar':
            # alvo deve ser notify.*
            target_domain = self.table.domain(a.notify_target)
            if target_domain != 'notify':
                self._error(
                    f"o alvo de 'notificar' deve ter domínio 'notify'; "
                    f"recebido: '{a.notify_target}' (domínio: '{target_domain}')",
                    line=a.line,
                )

        elif a.kind == 'aguardar':
            if a.duration and str(a.duration).startswith('-'):
                self._error(
                    f"duração de 'aguardar' não pode ser negativa: '{a.duration}'",
                    line=a.line,
                )

        elif a.kind == 'if':
            for c in a.conditions:
                self._check_condition(c)
            for sub in a.then_actions + a.else_actions:
                self._check_action(sub)

        elif a.kind == 'escolher':
            for ch in a.choices:
                for c in ch.conditions:
                    self._check_condition(c)
                for sub in ch.actions:
                    self._check_action(sub)

    # ---------------------------------------------------------- utilitário

    def _check_entity_domain(self, entity_id: str, line: int):
        if entity_id and not self.table.is_known_domain(entity_id):
            self._error(
                f"domínio desconhecido: '{self.table.domain(entity_id)}' "
                f"em '{entity_id}'",
                line=line,
            )
