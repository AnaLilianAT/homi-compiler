"""
Analisador Sintático (Parser) — Linguagem Homi
Implementado com PLY yacc, gerando tabela LALR(1) automaticamente.

A tabela gerada fica em parsetab.py (útil para o relatório).
Conflitos shift-reduce esperados (resolvidos por shift, comportamento correto):
  - optional suffix COMO STRING em triggers
  - optional suffix BRILHO NUMBER PORCENTO em 'ligar'
  - optional OFFSET DURACAO em sun_event

Recuperação de erros (Modo Pânico):
  As produções *_error sincronizam em trigger/condition/action seguinte ao erro,
  permitindo que o parser continue sem abortar no primeiro erro.
"""

import ply.yacc as yacc
from lexer import tokens, build_lexer          # tokens importado para PLY
from ast_nodes import (
    ProgramNode, AutomationNode,
    TriggerNode, ConditionNode,
    ActionNode, ChoiceNode,
)
from errors import ErroSintatico

# Referência global ao parser (necessária em p_error para errok)
_parser = None
_parse_errors: list[ErroSintatico] = []


# ===========================================================================
# program
# ===========================================================================

def p_program(p):
    '''program : automation_list'''
    p[0] = ProgramNode(automations=p[1])


# ===========================================================================
# automation_list
# ===========================================================================

def p_automation_list_one(p):
    '''automation_list : automation'''
    p[0] = [p[1]]


def p_automation_list_many(p):
    '''automation_list : automation_list automation'''
    p[0] = p[1] + [p[2]]


# ===========================================================================
# automation
# ===========================================================================

def p_automation(p):
    '''automation : AUTOMACAO STRING LBRACE body RBRACE'''
    triggers, conditions, actions, mode = p[4]
    p[0] = AutomationNode(
        name=p[2],
        triggers=triggers,
        conditions=conditions,
        actions=actions,
        mode=mode,
        line=p.lineno(1),
    )


# ===========================================================================
# body   →   when_section  opt_se_section  opt_faca_section  opt_modo_section
# ===========================================================================

def p_body(p):
    '''body : when_section opt_se_section opt_faca_section opt_modo_section'''
    p[0] = (p[1], p[2], p[3], p[4])


# ===========================================================================
# when_section
# ===========================================================================

def p_when_section(p):
    '''when_section : QUANDO COLON trigger_list'''
    p[0] = p[3]


# ---------------------------------------------------------------------------
# trigger_list
# ---------------------------------------------------------------------------

def p_trigger_list_one(p):
    '''trigger_list : trigger'''
    p[0] = [p[1]]


def p_trigger_list_many(p):
    '''trigger_list : trigger_list trigger'''
    p[0] = p[1] + [p[2]]


# Recuperação de erro: descarta token problemático e tenta ler próximo trigger
def p_trigger_list_error(p):
    '''trigger_list : trigger_list error trigger'''
    _add_error(ErroSintatico("gatilho inválido ignorado (modo pânico)"))
    p[0] = p[1] + [p[3]]


# ---------------------------------------------------------------------------
# triggers
# ---------------------------------------------------------------------------

def p_trigger_entity(p):
    '''trigger : domain_kw ENTITY_ID MUDA_PARA state_value'''
    p[0] = TriggerNode(kind='state', entity=p[2], to=p[4], line=p.lineno(2))


def p_trigger_entity_id(p):
    '''trigger : domain_kw ENTITY_ID MUDA_PARA state_value COMO STRING'''
    p[0] = TriggerNode(kind='state', entity=p[2], to=p[4], trigger_id=p[6], line=p.lineno(2))


def p_trigger_time(p):
    '''trigger : AO_HORARIO TIME'''
    p[0] = TriggerNode(kind='time', at=p[2], line=p.lineno(1))


def p_trigger_time_id(p):
    '''trigger : AO_HORARIO TIME COMO STRING'''
    p[0] = TriggerNode(kind='time', at=p[2], trigger_id=p[4], line=p.lineno(1))


def p_trigger_sun(p):
    '''trigger : sun_event'''
    p[0] = p[1]


# sun_event: por_do_sol / nascer_do_sol com offset e/ou id opcionais
# (shift-reduce esperado — PLY escolhe shift = match mais longo)

def p_sun_event_bare(p):
    '''sun_event : POR_DO_SOL
                 | NASCER_DO_SOL'''
    p[0] = TriggerNode(kind='sun', sun_event=p[1], line=p.lineno(1))


def p_sun_event_id(p):
    '''sun_event : POR_DO_SOL COMO STRING
                 | NASCER_DO_SOL COMO STRING'''
    p[0] = TriggerNode(kind='sun', sun_event=p[1], trigger_id=p[3], line=p.lineno(1))


def p_sun_event_offset(p):
    '''sun_event : POR_DO_SOL OFFSET DURACAO
                 | NASCER_DO_SOL OFFSET DURACAO'''
    p[0] = TriggerNode(kind='sun', sun_event=p[1], offset=p[3], line=p.lineno(1))


def p_sun_event_offset_id(p):
    '''sun_event : POR_DO_SOL OFFSET DURACAO COMO STRING
                 | NASCER_DO_SOL OFFSET DURACAO COMO STRING'''
    p[0] = TriggerNode(kind='sun', sun_event=p[1], offset=p[3], trigger_id=p[5], line=p.lineno(1))


def p_domain_kw(p):
    '''domain_kw : SENSOR
                 | LUZ
                 | INTERRUPTOR
                 | ALARME
                 | MEDIA
                 | TIMER'''
    p[0] = p[1]


# ===========================================================================
# opt_se_section
# ===========================================================================

def p_opt_se_section_some(p):
    '''opt_se_section : se_section'''
    p[0] = p[1]


def p_opt_se_section_empty(p):
    '''opt_se_section :'''
    p[0] = []


def p_se_section(p):
    '''se_section : SE COLON condition_list'''
    p[0] = p[3]


# ---------------------------------------------------------------------------
# condition_list
# ---------------------------------------------------------------------------

def p_condition_list_one(p):
    '''condition_list : condition'''
    p[0] = [p[1]]


def p_condition_list_many(p):
    '''condition_list : condition_list condition'''
    p[0] = p[1] + [p[2]]


# Recuperação de erro: descarta token problemático e tenta ler próxima condição
def p_condition_list_error(p):
    '''condition_list : condition_list error condition'''
    _add_error(ErroSintatico("condição inválida ignorada (modo pânico)"))
    p[0] = p[1] + [p[3]]


# ---------------------------------------------------------------------------
# conditions
# ---------------------------------------------------------------------------

def p_condition_state(p):
    '''condition : ENTITY_ID ESTA state_value'''
    p[0] = ConditionNode(kind='state', entity=p[1], state=p[3], line=p.lineno(1))


def p_condition_state_domain(p):
    '''condition : domain_kw ENTITY_ID ESTA state_value'''
    # Forma legível para leigos: "interruptor switch.sala esta desligado"
    p[0] = ConditionNode(kind='state', entity=p[2], state=p[4], line=p.lineno(2))


def p_condition_time(p):
    '''condition : HORARIO ENTRE TIME E TIME'''
    p[0] = ConditionNode(kind='time', after=p[3], before=p[5], line=p.lineno(1))


# ===========================================================================
# opt_faca_section
# ===========================================================================

def p_opt_faca_section_some(p):
    '''opt_faca_section : faca_section'''
    p[0] = p[1]


def p_opt_faca_section_empty(p):
    '''opt_faca_section :'''
    p[0] = []


def p_faca_section(p):
    '''faca_section : FACA COLON action_list'''
    p[0] = p[3]


# ---------------------------------------------------------------------------
# action_list
# ---------------------------------------------------------------------------

def p_action_list_one(p):
    '''action_list : action'''
    p[0] = [p[1]]


def p_action_list_many(p):
    '''action_list : action_list action'''
    p[0] = p[1] + [p[2]]


# Recuperação de erro: descarta token problemático e tenta ler próxima ação
def p_action_list_error(p):
    '''action_list : action_list error action'''
    _add_error(ErroSintatico("ação inválida ignorada (modo pânico)"))
    p[0] = p[1] + [p[3]]


# ---------------------------------------------------------------------------
# actions
# ---------------------------------------------------------------------------

def p_action_ligar(p):
    '''action : LIGAR ENTITY_ID'''
    p[0] = ActionNode(kind='ligar', entity=p[2], line=p.lineno(1))


def p_action_ligar_brilho(p):
    '''action : LIGAR ENTITY_ID BRILHO NUMBER PORCENTO'''
    p[0] = ActionNode(kind='ligar', entity=p[2], brightness=int(p[4]), line=p.lineno(1))


def p_action_desligar(p):
    '''action : DESLIGAR ENTITY_ID'''
    p[0] = ActionNode(kind='desligar', entity=p[2], line=p.lineno(1))


def p_action_aguardar(p):
    '''action : AGUARDAR DURACAO'''
    p[0] = ActionNode(kind='aguardar', duration=str(p[2]), line=p.lineno(1))


def p_action_notificar(p):
    '''action : NOTIFICAR STRING PARA ENTITY_ID'''
    p[0] = ActionNode(kind='notificar', message=p[2], notify_target=p[4], line=p.lineno(1))


def p_action_if(p):
    '''action : SE condition_list ENTAO COLON action_list FIM'''
    p[0] = ActionNode(kind='if', conditions=p[2], then_actions=p[5], line=p.lineno(1))


def p_action_if_else(p):
    '''action : SE condition_list ENTAO COLON action_list SENAO COLON action_list FIM'''
    p[0] = ActionNode(
        kind='if',
        conditions=p[2],
        then_actions=p[5],
        else_actions=p[8],
        line=p.lineno(1),
    )


def p_action_escolher(p):
    '''action : ESCOLHER COLON choice_list FIM'''
    p[0] = ActionNode(kind='escolher', choices=p[3], line=p.lineno(1))


# ---------------------------------------------------------------------------
# choice_list  /  choice
# ---------------------------------------------------------------------------

def p_choice_list_one(p):
    '''choice_list : choice'''
    p[0] = [p[1]]


def p_choice_list_many(p):
    '''choice_list : choice_list choice'''
    p[0] = p[1] + [p[2]]


def p_choice(p):
    '''choice : CASO condition_list FACA COLON action_list'''
    p[0] = ChoiceNode(conditions=p[2], actions=p[5], line=p.lineno(1))


# ===========================================================================
# opt_modo_section
# ===========================================================================

def p_opt_modo_section_some(p):
    '''opt_modo_section : modo_section'''
    p[0] = p[1]


def p_opt_modo_section_empty(p):
    '''opt_modo_section :'''
    p[0] = 'single'   # padrão Home Assistant


def p_modo_section(p):
    '''modo_section : MODO COLON modo_value'''
    p[0] = p[3]


def p_modo_value(p):
    '''modo_value : UNICO
                  | REINICIAR
                  | FILA
                  | PARALELO'''
    _map = {
        'unico':     'single',
        'reiniciar': 'restart',
        'fila':      'queued',
        'paralelo':  'parallel',
    }
    p[0] = _map[p[1]]


# ===========================================================================
# state_value — aceita PT, EN e strings/números genéricos
# ===========================================================================

_STATE_MAP = {
    'on':         'on',
    'off':        'off',
    'ligado':     'on',
    'ligada':     'on',        # feminino PT
    'desligado':  'off',
    'desligada':  'off',       # feminino PT
    'armado':     'armed_home',
    'armada':     'armed_home',
    'desarmado':  'disarmed',
    'desarmada':  'disarmed',
}


def p_state_value(p):
    '''state_value : ON
                   | OFF
                   | LIGADO
                   | DESLIGADO
                   | ARMADO
                   | DESARMADO
                   | STRING
                   | NUMBER'''
    val = p[1]
    if isinstance(val, str):
        p[0] = _STATE_MAP.get(val.lower(), val)
    else:
        p[0] = val


# ===========================================================================
# Tratamento de erros sintáticos (reporta e continua — Modo Pânico)
# ===========================================================================

def p_error(p):
    if p:
        err = ErroSintatico(
            f"token inesperado '{p.value}' (tipo: {p.type})",
            line=p.lineno,
        )
        _add_error(err)
        # Sinaliza ao PLY que o erro foi tratado; as produções *_error
        # cuidam da sincronização de tokens
        _parser.errok()
    else:
        _add_error(ErroSintatico("fim de arquivo inesperado"))


# ===========================================================================
# Utilitários internos
# ===========================================================================

def _add_error(err: ErroSintatico):
    print(err)
    _parse_errors.append(err)


# ===========================================================================
# Fábrica pública
# ===========================================================================

def build_parser(debug: bool = False, **kwargs) -> yacc.LRParser:
    """
    Constrói e devolve o parser LALR(1).

    A tabela LALR(1) é gravada em parsetab.py na primeira execução.
    O arquivo parser.out contém o relatório de conflitos (útil para o relatório).
    """
    global _parser, _parse_errors
    _parse_errors = []
    _parser = yacc.yacc(debug=debug, **kwargs)
    return _parser


def get_parse_errors() -> list[ErroSintatico]:
    """Retorna os erros coletados na última chamada ao parser."""
    return list(_parse_errors)
