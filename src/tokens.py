from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    ENTIDADE = auto()
    DISPOSITIVO = auto()
    AUTOMACAO = auto()
    MODO = auto()
    DESCRICAO = auto()
    GATILHOS = auto()
    CONDICOES = auto()
    ACOES = auto()
    QUANDO = auto()
    SE = auto()
    FACA = auto()
    ESPERE = auto()
    ESTADO = auto()
    SOL = auto()
    HORA = auto()
    HORARIO = auto()
    GATILHO = auto()
    PARA = auto()
    DE = auto()
    ATE = auto()
    ENTRE = auto()
    E = auto()
    EM = auto()
    IGUAL = auto()
    ANTES = auto()
    DEPOIS = auto()
    OFFSET = auto()
    LIGADO = auto()
    DESLIGADO = auto()
    ABERTA = auto()
    FECHADA = auto()
    ABERTO = auto()
    FECHADO = auto()
    ARMADO = auto()
    DESARMADO = auto()
    MOVIMENTO = auto()
    BATERIA = auto()
    VOLUME_FLUXO = auto()
    ACIMA = auto()
    ABAIXO = auto()
    QUALQUER = auto()
    TODOS = auto()
    ENTAO = auto()
    SENAO = auto()
    ESCOLHA = auto()
    CASO = auto()
    LIGAR = auto()
    DESLIGAR = auto()
    ALTERNAR = auto()
    ABRIR = auto()
    FECHAR = auto()
    SERVICO = auto()
    ALVO = auto()
    DADOS = auto()
    METADADOS = auto()
    TRUE = auto()
    FALSE = auto()
    SINGLE = auto()
    RESTART = auto()
    POR_DO_SOL = auto()
    NASCER_DO_SOL = auto()
    POR = auto()
    DIAS = auto()
    ID = auto()
    APELIDO = auto()
    HABILITADO = auto()
    DEVICE_ID = auto()
    ENTITY_ID = auto()

    IDENTIFIER = auto()
    DOTTED_ID = auto()
    STRING = auto()
    NUMBER = auto()
    DURATION = auto()

    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LPAREN = auto()
    RPAREN = auto()
    COLON = auto()
    SEMICOLON = auto()
    COMMA = auto()
    ASSIGN = auto()
    DOT = auto()
    NEWLINE = auto()
    EOF = auto()


KEYWORDS: dict[str, TokenType] = {
    "entidade": TokenType.ENTIDADE,
    "dispositivo": TokenType.DISPOSITIVO,
    "automacao": TokenType.AUTOMACAO,
    "modo": TokenType.MODO,
    "descricao": TokenType.DESCRICAO,
    "gatilhos": TokenType.GATILHOS,
    "condicoes": TokenType.CONDICOES,
    "acoes": TokenType.ACOES,
    "quando": TokenType.QUANDO,
    "se": TokenType.SE,
    "faca": TokenType.FACA,
    "espere": TokenType.ESPERE,
    "estado": TokenType.ESTADO,
    "sol": TokenType.SOL,
    "hora": TokenType.HORA,
    "horario": TokenType.HORARIO,
    "gatilho": TokenType.GATILHO,
    "para": TokenType.PARA,
    "de": TokenType.DE,
    "ate": TokenType.ATE,
    "entre": TokenType.ENTRE,
    "e": TokenType.E,
    "em": TokenType.EM,
    "igual": TokenType.IGUAL,
    "antes": TokenType.ANTES,
    "depois": TokenType.DEPOIS,
    "offset": TokenType.OFFSET,
    "ligado": TokenType.LIGADO,
    "desligado": TokenType.DESLIGADO,
    "aberta": TokenType.ABERTA,
    "fechada": TokenType.FECHADA,
    "aberto": TokenType.ABERTO,
    "fechado": TokenType.FECHADO,
    "armado": TokenType.ARMADO,
    "desarmado": TokenType.DESARMADO,
    "movimento": TokenType.MOVIMENTO,
    "bateria": TokenType.BATERIA,
    "volume_fluxo": TokenType.VOLUME_FLUXO,
    "acima": TokenType.ACIMA,
    "abaixo": TokenType.ABAIXO,
    "qualquer": TokenType.QUALQUER,
    "todos": TokenType.TODOS,
    "entao": TokenType.ENTAO,
    "senao": TokenType.SENAO,
    "escolha": TokenType.ESCOLHA,
    "caso": TokenType.CASO,
    "ligar": TokenType.LIGAR,
    "desligar": TokenType.DESLIGAR,
    "alternar": TokenType.ALTERNAR,
    "abrir": TokenType.ABRIR,
    "fechar": TokenType.FECHAR,
    "servico": TokenType.SERVICO,
    "alvo": TokenType.ALVO,
    "dados": TokenType.DADOS,
    "metadados": TokenType.METADADOS,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "single": TokenType.SINGLE,
    "restart": TokenType.RESTART,
    "por_do_sol": TokenType.POR_DO_SOL,
    "nascer_do_sol": TokenType.NASCER_DO_SOL,
    "por": TokenType.POR,
    "dias": TokenType.DIAS,
    "id": TokenType.ID,
    "apelido": TokenType.APELIDO,
    "habilitado": TokenType.HABILITADO,
    "device_id": TokenType.DEVICE_ID,
    "entity_id": TokenType.ENTITY_ID,
}


SYMBOLS: dict[str, TokenType] = {
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    "[": TokenType.LBRACKET,
    "]": TokenType.RBRACKET,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    ":": TokenType.COLON,
    ";": TokenType.SEMICOLON,
    ",": TokenType.COMMA,
    "=": TokenType.ASSIGN,
    ".": TokenType.DOT,
}


@dataclass(slots=True, frozen=True)
class Token:
    token_type: TokenType
    lexeme: str
    line: int
    column: int
