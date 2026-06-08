"""
Analisador Léxico (Scanner) — Linguagem Homi
Implementado com PLY lex (DFA gerado automaticamente).

Ordem de prioridade dos tokens em PLY:
  1. Funções (por ordem de definição no arquivo)
  2. Strings (por comprimento decrescente)

Por isso t_ENTITY_ID e t_DURACAO são funções e vêm antes de t_ID e t_NUMBER.
"""

import ply.lex as lex
from errors import ErroLexico

# ---------------------------------------------------------------------------
# Palavras reservadas → tipo de token
# ---------------------------------------------------------------------------

reserved = {
    # Estrutura da automação
    'automacao':     'AUTOMACAO',
    'quando':        'QUANDO',
    'se':            'SE',
    'faca':          'FACA',
    'modo':          'MODO',
    # Ações
    'ligar':         'LIGAR',
    'desligar':      'DESLIGAR',
    'aguardar':      'AGUARDAR',
    'notificar':     'NOTIFICAR',
    'para':          'PARA',
    # Controle de fluxo
    'entao':         'ENTAO',
    'senao':         'SENAO',
    'fim':           'FIM',
    'escolher':      'ESCOLHER',
    'caso':          'CASO',
    # Predicado de condição
    'esta':          'ESTA',
    'muda_para':     'MUDA_PARA',
    'como':          'COMO',
    # Tipos de domínio (prefixo de gatilho)
    'sensor':        'SENSOR',
    'luz':           'LUZ',
    'interruptor':   'INTERRUPTOR',
    'alarme':        'ALARME',
    'media':         'MEDIA',
    'timer':         'TIMER',
    # Tempo
    'horario':       'HORARIO',
    'ao_horario':    'AO_HORARIO',
    'entre':         'ENTRE',
    'e':             'E',
    # Gatilhos solares
    'nascer_do_sol': 'NASCER_DO_SOL',
    'por_do_sol':    'POR_DO_SOL',
    'offset':        'OFFSET',
    # Parâmetro de brilho
    'brilho':        'BRILHO',
    # Modos de execução
    'unico':         'UNICO',
    'reiniciar':     'REINICIAR',
    'fila':          'FILA',
    'paralelo':      'PARALELO',
    # Estados (PT masculino, feminino e EN — mesmos tokens)
    'on':            'ON',
    'off':           'OFF',
    'ligado':        'LIGADO',
    'ligada':        'LIGADO',      # feminino PT
    'desligado':     'DESLIGADO',
    'desligada':     'DESLIGADO',   # feminino PT
    'armado':        'ARMADO',
    'armada':        'ARMADO',      # feminino PT
    'desarmado':     'DESARMADO',
    'desarmada':     'DESARMADO',   # feminino PT
}

# ---------------------------------------------------------------------------
# Lista completa de tokens (obrigatória para PLY)
# ---------------------------------------------------------------------------

_literal_tokens = [
    'ENTITY_ID',   # domain.entity_name
    'TIME',        # HH:MM ou HH:MM:SS
    'DURACAO',     # 45s, 4min, -1h30, -45min
    'NUMBER',      # 80, 3.14
    'PORCENTO',    # %
    'STRING',      # "texto" ou 'texto'
    'LBRACE',      # {
    'RBRACE',      # }
    'COLON',       # :
]
# dict.values() pode ter duplicatas (formas femininas → mesmo token)
tokens = list(dict.fromkeys(reserved.values())) + _literal_tokens

# ---------------------------------------------------------------------------
# Tokens simples (string)
# ---------------------------------------------------------------------------

t_LBRACE   = r'\{'
t_RBRACE   = r'\}'
t_COLON    = r':'
t_PORCENTO = r'%'

# ---------------------------------------------------------------------------
# Tokens complexos (funções — prioridade por ordem de definição)
# ---------------------------------------------------------------------------

def t_ENTITY_ID(t):
    r'[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_.]*'
    # entity_id sempre tem ponto: light.sala, binary_sensor.motion_x
    # Deve ser testado ANTES de t_ID para não partir em "binary_sensor" + erro
    return t


def t_DURACAO(t):
    r'-?\d+h\d+|-?\d+(?:ms|s|min|h)'
    # Grupo 1: -1h30, -1h15 (horas + minutos sem sufixo)
    # Grupo 2: 45s, 4min, -45min, 500ms
    # Deve vir ANTES de t_NUMBER para capturar "45s" inteiro
    return t


def t_TIME(t):
    r'\d{2}:\d{2}(?::\d{2})?'
    # 01:15, 06:30, 23:00:00
    # Deve vir ANTES de t_COLON para não partir "01:15" em NUMBER+COLON+NUMBER
    return t


def t_NUMBER(t):
    r'\d+(?:\.\d+)?'
    t.value = float(t.value) if '.' in str(t.value) else int(t.value)
    return t


def t_STRING(t):
    r'"[^"\n]*"|\'[^\'\n]*\''
    t.value = t.value[1:-1]   # remove aspas
    return t


def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    # Verifica se é palavra reservada; caso contrário é erro léxico
    t.type = reserved.get(t.value, None)
    if t.type is None:
        _add_error(t.lexer, ErroLexico(
            f"identificador desconhecido '{t.value}'", line=t.lineno
        ))
        return None   # descarta token — PLY continua lexando
    return t


# ---------------------------------------------------------------------------
# Descartados
# ---------------------------------------------------------------------------

def t_COMMENT(t):
    r'//[^\n]*'
    pass   # comentário de linha — descartado


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


t_ignore = ' \t\r'


# ---------------------------------------------------------------------------
# Erro léxico (caractere inválido)
# ---------------------------------------------------------------------------

def t_error(t):
    _add_error(t.lexer, ErroLexico(
        f"caractere inválido '{t.value[0]}'", line=t.lineno
    ))
    t.lexer.skip(1)


# ---------------------------------------------------------------------------
# Utilitário interno
# ---------------------------------------------------------------------------

def _add_error(lexer, err: ErroLexico):
    print(err)
    lexer.lex_errors.append(err)


# ---------------------------------------------------------------------------
# Fábrica pública
# ---------------------------------------------------------------------------

def build_lexer(**kwargs) -> lex.Lexer:
    """Constrói e devolve um lexer PLY com lista de erros embutida."""
    lexer = lex.lex(**kwargs)
    lexer.lex_errors: list[ErroLexico] = []
    return lexer
