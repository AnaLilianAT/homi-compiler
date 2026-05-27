from src.ast_nodes import ChooseAction, IfAction, ServiceAction, StateTrigger
from src.parser_ll1 import LL1Parser
from src.scanner import Scanner


def parse_source(source: str):
    scanner_result = Scanner(source).scan_tokens()
    parser = LL1Parser()
    program = parser.parse(scanner_result.tokens)
    return scanner_result, parser, program


def test_parser_parses_simple_automation() -> None:
    source = """
automacao "Sala" modo single {
    descricao "Liga a sala";
    gatilhos {
        quando estado [binary_sensor.movimento_sala] para ["on"] id "Movimento";
    }
    acoes {
        faca servico light.turn_on alvo {
            entity_id: [light.sala];
        } dados {
        };
    }
}
"""

    scanner_result, parser, program = parse_source(source)

    assert scanner_result.diagnostics == []
    assert parser.diagnostics == []
    assert len(program.automations) == 1
    assert program.automations[0].alias == "Sala"
    assert isinstance(program.automations[0].triggers[0], StateTrigger)
    assert isinstance(program.automations[0].actions[0], ServiceAction)


def test_parser_parses_multiple_automations() -> None:
    source = """
automacao "A1" modo single {
    acoes {
        espere 45s;
    }
}

automacao "A2" modo restart {
    acoes {
        espere 1h;
    }
}
"""

    scanner_result, parser, program = parse_source(source)

    assert scanner_result.diagnostics == []
    assert parser.diagnostics == []
    assert [automation.alias for automation in program.automations] == ["A1", "A2"]


def test_parser_parses_if_then_else() -> None:
    source = """
automacao "Faixa" modo single {
    acoes {
        se horario entre "01:15:00" e "12:00:00" entao {
            espere 45s;
        } senao {
            espere 1h;
        }
    }
}
"""

    _, parser, program = parse_source(source)

    assert parser.diagnostics == []
    assert isinstance(program.automations[0].actions[0], IfAction)
    assert len(program.automations[0].actions[0].then_actions) == 1
    assert len(program.automations[0].actions[0].else_actions) == 1


def test_parser_parses_choose() -> None:
    source = """
automacao "Escolha" modo single {
    acoes {
        escolha {
            caso gatilho em ["sol"] {
                faca servico automation.trigger alvo {
                    entity_id: [automation.cozinha_ligar_luzes];
                } dados {
                    skip_condition: true;
                };
            }
        }
    }
}
"""

    _, parser, program = parse_source(source)

    assert parser.diagnostics == []
    assert isinstance(program.automations[0].actions[0], ChooseAction)
    assert len(program.automations[0].actions[0].cases) == 1


def test_parser_reports_syntax_error_with_recovery() -> None:
    source = """
automacao "Com erro" modo single {
    acoes {
        faca servico light.turn_on alvo {
            entity_id: [light.sala]
        } dados {
        }
    }
}
"""

    _, parser, _ = parse_source(source)

    assert parser.diagnostics


def test_parser_continues_after_error() -> None:
    source = """
automacao "Quebrada" modo single {
    acoes {
        faca servico light.turn_on alvo {
            entity_id: [light.sala]
        } dados {
        }
    }
}

automacao "Valida" modo single {
    acoes {
        espere 45s;
    }
}
"""

    _, parser, program = parse_source(source)

    assert parser.diagnostics
    assert any(automation.alias == "Valida" for automation in program.automations)
