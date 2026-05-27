from src.scanner import Scanner
from src.tokens import TokenType


def test_scanner_returns_eof_for_empty_input() -> None:
    result = Scanner("").scan_tokens()

    assert result.diagnostics == []
    assert [token.token_type for token in result.tokens] == [TokenType.EOF]


def test_scanner_recognizes_keywords() -> None:
    source = (
        "entidade dispositivo automacao modo descricao "
        "gatilhos condicoes acoes quando se faca espere estado sol hora horario "
        "gatilho para de ate entre e em igual antes depois offset ligado desligado "
        "aberta fechada movimento bateria volume_fluxo acima abaixo qualquer todos "
        "armado desarmado "
        "entao senao escolha caso ligar desligar alternar abrir fechar servico alvo "
        "dados true false single restart por_do_sol nascer_do_sol"
    )

    result = Scanner(source).scan_tokens()

    assert result.diagnostics == []
    assert [token.token_type for token in result.tokens[:-1]] == [
        TokenType.ENTIDADE,
        TokenType.DISPOSITIVO,
        TokenType.AUTOMACAO,
        TokenType.MODO,
        TokenType.DESCRICAO,
        TokenType.GATILHOS,
        TokenType.CONDICOES,
        TokenType.ACOES,
        TokenType.QUANDO,
        TokenType.SE,
        TokenType.FACA,
        TokenType.ESPERE,
        TokenType.ESTADO,
        TokenType.SOL,
        TokenType.HORA,
        TokenType.HORARIO,
        TokenType.GATILHO,
        TokenType.PARA,
        TokenType.DE,
        TokenType.ATE,
        TokenType.ENTRE,
        TokenType.E,
        TokenType.EM,
        TokenType.IGUAL,
        TokenType.ANTES,
        TokenType.DEPOIS,
        TokenType.OFFSET,
        TokenType.LIGADO,
        TokenType.DESLIGADO,
        TokenType.ABERTA,
        TokenType.FECHADA,
        TokenType.MOVIMENTO,
        TokenType.BATERIA,
        TokenType.VOLUME_FLUXO,
        TokenType.ACIMA,
        TokenType.ABAIXO,
        TokenType.QUALQUER,
        TokenType.TODOS,
        TokenType.ARMADO,
        TokenType.DESARMADO,
        TokenType.ENTAO,
        TokenType.SENAO,
        TokenType.ESCOLHA,
        TokenType.CASO,
        TokenType.LIGAR,
        TokenType.DESLIGAR,
        TokenType.ALTERNAR,
        TokenType.ABRIR,
        TokenType.FECHAR,
        TokenType.SERVICO,
        TokenType.ALVO,
        TokenType.DADOS,
        TokenType.TRUE,
        TokenType.FALSE,
        TokenType.SINGLE,
        TokenType.RESTART,
        TokenType.POR_DO_SOL,
        TokenType.NASCER_DO_SOL,
    ]


def test_scanner_recognizes_identifiers_and_dotted_ids() -> None:
    source = "luz_sala movimento_corredor timer_closet light.corda_led_corredor notify.mobile_app_zfold4"

    result = Scanner(source).scan_tokens()

    assert result.diagnostics == []
    assert [token.token_type for token in result.tokens[:-1]] == [
        TokenType.IDENTIFIER,
        TokenType.IDENTIFIER,
        TokenType.IDENTIFIER,
        TokenType.DOTTED_ID,
        TokenType.DOTTED_ID,
    ]


def test_scanner_recognizes_strings_durations_and_numbers() -> None:
    source = '"Movimento noturno na sala" 45s 4min 1h 1min45s 20 0.5'

    result = Scanner(source).scan_tokens()

    assert result.diagnostics == []
    assert [token.token_type for token in result.tokens[:-1]] == [
        TokenType.STRING,
        TokenType.DURATION,
        TokenType.DURATION,
        TokenType.DURATION,
        TokenType.DURATION,
        TokenType.NUMBER,
        TokenType.NUMBER,
    ]
    assert result.tokens[0].lexeme == '"Movimento noturno na sala"'
    assert result.tokens[5].lexeme == "20"
    assert result.tokens[6].lexeme == "0.5"


def test_scanner_ignores_comments_and_keeps_newlines() -> None:
    source = 'entidade luz = light.sala; # comentario\n# linha inteira\nacoes'

    result = Scanner(source).scan_tokens()

    assert result.diagnostics == []
    assert [token.token_type for token in result.tokens] == [
        TokenType.ENTIDADE,
        TokenType.IDENTIFIER,
        TokenType.ASSIGN,
        TokenType.DOTTED_ID,
        TokenType.SEMICOLON,
        TokenType.NEWLINE,
        TokenType.NEWLINE,
        TokenType.ACOES,
        TokenType.EOF,
    ]


def test_scanner_reports_lexical_error_without_stopping() -> None:
    result = Scanner("@ entidade").scan_tokens()

    assert len(result.diagnostics) == 1
    assert "Unexpected character '@'." == result.diagnostics[0].message
    assert [token.token_type for token in result.tokens] == [
        TokenType.ENTIDADE,
        TokenType.EOF,
    ]


def test_scanner_tracks_line_and_column_positions() -> None:
    source = "entidade luz = light.sala;\n    faca servico timer.start;\n"

    result = Scanner(source).scan_tokens()

    assert result.diagnostics == []
    assert [(token.lexeme, token.line, token.column) for token in result.tokens[:-1]] == [
        ("entidade", 1, 1),
        ("luz", 1, 10),
        ("=", 1, 14),
        ("light.sala", 1, 16),
        (";", 1, 26),
        ("\n", 1, 27),
        ("faca", 2, 5),
        ("servico", 2, 10),
        ("timer.start", 2, 18),
        (";", 2, 29),
        ("\n", 2, 30),
    ]


def test_scanner_recognizes_symbols() -> None:
    result = Scanner("{ } [ ] ( ) : ; , = .").scan_tokens()

    assert result.diagnostics == []
    assert [token.token_type for token in result.tokens[:-1]] == [
        TokenType.LBRACE,
        TokenType.RBRACE,
        TokenType.LBRACKET,
        TokenType.RBRACKET,
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.COLON,
        TokenType.SEMICOLON,
        TokenType.COMMA,
        TokenType.ASSIGN,
        TokenType.DOT,
    ]
