"""
Gerador de Código Intermediário (YAML) — Linguagem Homi

Percorre a AST produzida pelo parser e emite YAML compatível com o
formato de automações do Home Assistant (versão 2024+).

Mapeamentos principais:
  ligar   → <domain>.turn_on   (cover → cover.open_cover, timer → timer.start)
  desligar→ <domain>.turn_off  (cover → cover.close_cover, timer → timer.cancel)
  aguardar→ delay: {seconds/minutes/hours/milliseconds}
  notificar → action: notify.<entity>
  se/entao/senao → if / then / else
  escolher/caso → choose / conditions / sequence
"""

import re
import yaml
from ast_nodes import (
    ProgramNode, AutomationNode,
    TriggerNode, ConditionNode,
    ActionNode, ChoiceNode,
)


# ---------------------------------------------------------------------------
# YAML Dumper customizado
# ---------------------------------------------------------------------------

class _HomiDumper(yaml.Dumper):
    """
    Força aspas simples em strings que o YAML padrão interpretaria como
    booleanos ou outros tipos escalares ('on', 'off', 'true', horários…).
    """
    pass


def _str_repr(dumper, data):
    # Strings que YAML converte para bool/null sem aspas
    needs_quote = {
        'on', 'off', 'true', 'false', 'yes', 'no',
        'null', 'True', 'False', 'ON', 'OFF',
    }
    # Horários (HH:MM:SS) também podem ser mal interpretados
    is_time = bool(re.fullmatch(r'\d{2}:\d{2}(?::\d{2})?', data))
    # Offsets (-01:30:00)
    is_offset = bool(re.fullmatch(r'-?\d{2}:\d{2}:\d{2}', data))

    if data in needs_quote or is_time or is_offset:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style="'")
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


_HomiDumper.add_representer(str, _str_repr)


# ---------------------------------------------------------------------------
# Gerador principal
# ---------------------------------------------------------------------------

class YAMLGenerator:

    def generate(self, program: ProgramNode) -> str:
        """Converte a AST inteira em string YAML."""
        entries = [self._automation(a) for a in program.automations]
        return yaml.dump(
            entries,
            Dumper=_HomiDumper,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )

    # ---------------------------------------------------------------- automação

    def _automation(self, auto: AutomationNode) -> dict:
        d: dict = {'alias': auto.name}
        d['triggers']   = [self._trigger(t)   for t in auto.triggers]
        d['conditions'] = [self._condition(c) for c in auto.conditions]
        d['actions']    = [self._action(a)    for a in auto.actions]
        d['mode']       = auto.mode
        return d

    # ---------------------------------------------------------------- triggers

    def _trigger(self, t: TriggerNode) -> dict:
        if t.kind == 'state':
            d: dict = {
                'trigger':   'state',
                'entity_id': t.entity,
                'to':        t.to,
            }
            if t.trigger_id:
                d['id'] = t.trigger_id
            return d

        if t.kind == 'time':
            d = {'trigger': 'time', 'at': _norm_time(t.at)}
            if t.trigger_id:
                d['id'] = t.trigger_id
            return d

        if t.kind == 'sun':
            event = 'sunset' if t.sun_event == 'por_do_sol' else 'sunrise'
            d = {'trigger': 'sun', 'event': event}
            if t.offset:
                d['offset'] = _offset_to_ha(t.offset)
            if t.trigger_id:
                d['id'] = t.trigger_id
            return d

        return {}

    # --------------------------------------------------------------- condições

    def _condition(self, c: ConditionNode) -> dict:
        if c.kind == 'state':
            return {
                'condition': 'state',
                'entity_id': c.entity,
                'state':     c.state,
            }
        if c.kind == 'time':
            return {
                'condition': 'time',
                'after':  _norm_time(c.after),
                'before': _norm_time(c.before),
            }
        return {}

    # ----------------------------------------------------------------- ações

    def _action(self, a: ActionNode) -> dict:

        if a.kind == 'ligar':
            domain = a.entity.split('.')[0]
            d: dict = {
                'action': _turn_on(domain),
                'target': {'entity_id': a.entity},
            }
            if a.brightness is not None:
                d['data'] = {'brightness_pct': a.brightness}
            return d

        if a.kind == 'desligar':
            domain = a.entity.split('.')[0]
            return {
                'action': _turn_off(domain),
                'target': {'entity_id': a.entity},
            }

        if a.kind == 'aguardar':
            return {'delay': _parse_dur(str(a.duration))}

        if a.kind == 'notificar':
            # a.notify_target já é notify.<xxx>
            notify_action = a.notify_target   # ex: notify.mobile_app_zfold4
            return {
                'action': notify_action,
                'data':   {'message': a.message},
            }

        if a.kind == 'if':
            d = {
                'if':   [self._condition(c) for c in a.conditions],
                'then': [self._action(x)    for x in a.then_actions],
            }
            if a.else_actions:
                d['else'] = [self._action(x) for x in a.else_actions]
            return d

        if a.kind == 'escolher':
            return {
                'choose': [
                    {
                        'conditions': [self._condition(c) for c in ch.conditions],
                        'sequence':   [self._action(x)   for x in ch.actions],
                    }
                    for ch in a.choices
                ]
            }

        return {}


# ---------------------------------------------------------------------------
# Funções auxiliares de conversão
# ---------------------------------------------------------------------------

def _norm_time(t: str) -> str:
    """Garante formato HH:MM:SS (adiciona :00 se necessário)."""
    if t and t.count(':') == 1:
        return t + ':00'
    return t or '00:00:00'


def _offset_to_ha(s: str) -> str:
    """
    Converte duração de offset Homi → string HA com sinal.
    Exemplos: '-1h30' → '-01:30:00',  '-45min' → '-00:45:00'
    """
    neg  = s.startswith('-')
    body = s.lstrip('-')
    sign = '-' if neg else ''

    m = re.fullmatch(r'(\d+)h(\d+)', body)
    if m:
        h, mn = int(m.group(1)), int(m.group(2))
        return f"{sign}{h:02d}:{mn:02d}:00"

    m = re.fullmatch(r'(\d+)(ms|s|min|h)', body)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        if unit == 'h':   return f"{sign}{n:02d}:00:00"
        if unit == 'min': return f"{sign}00:{n:02d}:00"
        if unit == 's':   return f"{sign}00:00:{n:02d}"

    return '00:00:00'


def _parse_dur(s: str) -> dict:
    """
    Converte duração Homi → dict de delay HA.
    Exemplos: '45s' → {seconds:45},  '4min' → {minutes:4},
              '1h30' → {hours:1, minutes:30}
    """
    body = s.lstrip('-')   # offset negativo não deveria chegar aqui

    m = re.fullmatch(r'(\d+)h(\d+)', body)
    if m:
        return {'hours': int(m.group(1)), 'minutes': int(m.group(2))}

    m = re.fullmatch(r'(\d+)(ms|s|min|h)', body)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        if unit == 'ms':  return {'milliseconds': n}
        if unit == 's':   return {'seconds': n}
        if unit == 'min': return {'minutes': n}
        if unit == 'h':   return {'hours': n}

    return {'seconds': 0}


def _turn_on(domain: str) -> str:
    _special = {'cover': 'cover.open_cover', 'timer': 'timer.start'}
    return _special.get(domain, f'{domain}.turn_on')


def _turn_off(domain: str) -> str:
    _special = {'cover': 'cover.close_cover', 'timer': 'timer.cancel'}
    return _special.get(domain, f'{domain}.turn_off')
