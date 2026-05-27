from pathlib import Path

from src.ast_nodes import ProgramNode
from src.parser_ll1 import LL1Parser
from src.scanner import Scanner
from src.semantic import SemanticAnalyzer


def analyze_source(source: str):
    scanner_result = Scanner(source).scan_tokens()
    parser = LL1Parser()
    program = parser.parse(scanner_result.tokens)
    diagnostics = SemanticAnalyzer().analyze(program)
    return scanner_result, parser, program, diagnostics


def test_semantic_base_has_no_diagnostics_for_empty_program() -> None:
    diagnostics = SemanticAnalyzer().analyze(ProgramNode())

    assert diagnostics == []


def test_semantic_accepts_valid_program_with_direct_ids() -> None:
    source = """
automacao "Sala" modo single {
    gatilhos {
        quando estado [binary_sensor.movimento_sala] para ["on"] id "Movimento";
        quando hora "05:00:00" id "Hora";
    }
    condicoes {
        se estado switch.luzes_da_sala igual ["off"];
        se gatilho em ["Movimento"];
    }
    acoes {
        faca servico timer.start alvo {
            entity_id: [timer.closet];
        } dados {
        };
        faca servico notify.mobile_app_zfold4 dados {
            message: "Sala ligada";
        };
    }
}
"""

    scanner_result, parser, _, diagnostics = analyze_source(source)

    assert scanner_result.diagnostics == []
    assert parser.diagnostics == []
    assert diagnostics == []


def test_semantic_accepts_valid_program_with_symbolic_declarations() -> None:
    source = """
entidade luz_sala = light.sala;
dispositivo cortina = cover device_id "dev-cover" entity_id "cover.sala";

automacao "Conforto" modo restart {
    gatilhos {
        quando sol por_do_sol id "sol";
    }
    condicoes {
        se estado luz_sala igual ["off"];
        se sol antes nascer_do_sol depois por_do_sol;
    }
    acoes {
        faca abrir cortina;
        faca servico automation.trigger alvo {
            entity_id: [automation.cozinha_ligar_luzes];
        } dados {
            skip_condition: true;
        };
    }
}
"""

    scanner_result, parser, _, diagnostics = analyze_source(source)

    assert scanner_result.diagnostics == []
    assert parser.diagnostics == []
    assert diagnostics == []


def test_semantic_reports_undefined_entity() -> None:
    source = """
automacao "Erro" modo single {
    condicoes {
        se estado luz_inexistente igual ["on"];
    }
    acoes {
        espere 45s;
    }
}
"""

    _, parser, _, diagnostics = analyze_source(source)

    assert parser.diagnostics == []
    assert any("Undefined entity symbol 'luz_inexistente'." == diagnostic.message for diagnostic in diagnostics)


def test_semantic_reports_wrong_action_for_sensor() -> None:
    source = """
dispositivo sensor_temp = sensor device_id "dev-sensor" entity_id "sensor.temperatura";

automacao "Erro sensor" modo single {
    acoes {
        faca ligar sensor_temp;
    }
}
"""

    _, parser, _, diagnostics = analyze_source(source)

    assert parser.diagnostics == []
    assert any("Action 'ligar' is not compatible with domain 'sensor'." == diagnostic.message for diagnostic in diagnostics)


def test_semantic_reports_unknown_trigger_id() -> None:
    source = """
automacao "Erro trigger" modo single {
    gatilhos {
        quando hora "05:00:00" id "Hora";
    }
    condicoes {
        se gatilho em ["Inexistente"];
    }
    acoes {
        espere 45s;
    }
}
"""

    _, parser, _, diagnostics = analyze_source(source)

    assert parser.diagnostics == []
    assert any("Unknown trigger id 'Inexistente' referenced in condition." == diagnostic.message for diagnostic in diagnostics)


def test_semantic_reports_invalid_timer_target() -> None:
    source = """
automacao "Erro timer" modo single {
    acoes {
        faca servico timer.start alvo {
            entity_id: [light.sala];
        } dados {
        };
    }
}
"""

    _, parser, _, diagnostics = analyze_source(source)

    assert parser.diagnostics == []
    assert any("Service 'timer.start' only accepts targets in domain 'timer'." == diagnostic.message for diagnostic in diagnostics)


def test_semantic_reports_invalid_mode_and_bad_time_trigger() -> None:
    source = """
automacao "Modo invalido" modo turbo {
    gatilhos {
        quando hora "25:61:00" id "Hora";
    }
    acoes {
        espere 45s;
    }
}
"""

    scanner_result = Scanner(source).scan_tokens()
    parser = LL1Parser()
    program = parser.parse(scanner_result.tokens)

    assert parser.diagnostics


def test_invalid_semantic_examples_exist() -> None:
    expected = {
        "undefined_entity.homi",
        "wrong_action_for_sensor.homi",
        "unknown_trigger_id.homi",
        "invalid_timer_target.homi",
    }

    found = {path.name for path in Path("examples/invalid_semantic").glob("*.homi")}

    assert expected.issubset(found)
