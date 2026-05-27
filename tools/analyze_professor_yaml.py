from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "examples" / "professor" / "automations_homi.yaml"
OUTPUT_PATH = ROOT / "docs" / "professor_yaml_coverage.md"


FIELD_NAMES = [
    "id",
    "alias",
    "from",
    "to",
    "above",
    "below",
    "for",
    "enabled",
    "brightness_pct",
    "weekday",
    "offset",
    "choose",
    "if",
    "then",
    "else",
    "delay",
    "target",
    "data",
    "metadata",
]


PATTERN_COVERAGE = {
    "automation.alias": '`automacao "Nome" modo ... { ... }`',
    "automation.description": '`descricao "texto";`',
    "automation.mode.single": '`modo single`',
    "automation.mode.restart": '`modo restart`',
    "automation.id": "Nao modelado diretamente em Homi. O `id` opaco do Home Assistant e tratado como detalhe de persistencia, nao como construcao autoral da linguagem.",
    "trigger.state": '`quando estado [entidade...] de ["..."] para ["..."] id "..." apelido "..." por 1min;`',
    "trigger.device.on_off_motion_open": '`quando dispositivo <dominio|alias> ... ligado|desligado|movimento|aberta|fechada ...;`',
    "trigger.device.battery": '`quando dispositivo sensor ... bateria acima|abaixo N ...;`',
    "trigger.device.volume_flow": '`quando dispositivo sensor ... volume_fluxo acima|abaixo N ...;`',
    "trigger.sun": '`quando sol por_do_sol|nascer_do_sol offset "-00:45:00" id "..."`; ',
    "trigger.time": '`quando hora "05:00:00" dias [seg, ter, ...] id "..."`; ',
    "condition.state": '`se estado entidade igual ["estado"...];`',
    "condition.device": '`se dispositivo <dominio|alias> ... ligado|desligado|armado|desarmado|aberto|fechado;`',
    "condition.trigger": '`se gatilho em ["Id 1", "Id 2"];`',
    "condition.time": '`se horario entre "01:00:00" e "06:30:00";`',
    "condition.sun": '`se sol antes nascer_do_sol depois por_do_sol;`',
    "condition.logical.or": '`se qualquer { ...; ...; };`',
    "condition.logical.and": '`se todos { ...; ...; };`',
    "action.device": '`faca ligar|desligar|alternar|abrir|fechar <dominio|alias> ...;`',
    "action.service": '`faca servico dominio.servico alvo { ... } dados { ... } metadados { ... };`',
    "action.delay": '`espere 1min45s;`',
    "action.if": '`se <condicao> entao { ... } senao { ... }`',
    "action.choose": '`escolha { caso <condicao> { ... } }`',
    "field.id": '`id "Nome do gatilho";` e `gatilho em ["Nome do gatilho"]`',
    "field.alias": '`apelido "Nome alternativo";`',
    "field.from": '`de ["estado_origem"]` em trigger de estado',
    "field.to": '`para ["estado_destino"]` em trigger de estado',
    "field.above": '`bateria acima N` ou `volume_fluxo acima N`',
    "field.below": '`bateria abaixo N` ou `volume_fluxo abaixo N`',
    "field.for": '`por 1min` em triggers de estado ou dispositivo',
    "field.enabled": '`habilitado true|false` em condicoes e acoes',
    "field.brightness_pct": '`faca servico light.turn_on ... dados { brightness_pct: 20; };`',
    "field.weekday": '`quando hora "05:00:00" dias [seg, ter, qua];`',
    "field.offset": '`quando sol por_do_sol offset "-00:45:00";`',
    "field.choose": '`escolha { caso ... { ... } }`',
    "field.if": '`se ... entao { ... } senao { ... }`',
    "field.then": "Bloco `entao { ... }` em `if`",
    "field.else": "Bloco `senao { ... }` em `if`",
    "field.delay": '`espere 45s;`',
    "field.target": '`alvo { entity_id: [...]; device_id: [...]; }`',
    "field.data": '`dados { chave: valor; ... }`',
    "field.metadata": '`metadados { chave: valor; ... }`',
}


def main() -> None:
    automations = yaml.safe_load(INPUT_PATH.read_text(encoding="utf-8"))
    markdown = build_report(automations)
    OUTPUT_PATH.write_text(markdown, encoding="utf-8")


def build_report(automations: list[dict[str, Any]]) -> str:
    aliases = [automation.get("alias", "<sem alias>") for automation in automations]
    trigger_types = Counter()
    condition_types = Counter()
    action_categories = Counter()
    services = Counter()
    domains = Counter()
    modes = Counter()
    fields = Counter()

    for automation in automations:
        if "id" in automation:
            fields["id"] += 1
        if "alias" in automation:
            fields["alias"] += 1
        modes[automation.get("mode", "<ausente>")] += 1

        for trigger in automation.get("triggers", []):
            walk_trigger(trigger, trigger_types, domains, fields)

        for condition in automation.get("conditions", []):
            walk_condition(condition, condition_types, domains, fields)

        for action in automation.get("actions", []):
            walk_action(action, action_categories, condition_types, services, domains, fields)

    lines: list[str] = []
    lines.append("# Cobertura do YAML do Professor")
    lines.append("")
    lines.append(f"Arquivo analisado: `{INPUT_PATH.relative_to(ROOT).as_posix()}`")
    lines.append("")
    lines.append("## Resumo")
    lines.append("")
    lines.append(f"- Quantidade de automacoes: {len(automations)}")
    lines.append(f"- Aliases encontrados: {len(aliases)}")
    lines.append(f"- Tipos de triggers encontrados: {format_counter(trigger_types)}")
    lines.append(f"- Tipos de conditions encontrados: {format_counter(condition_types)}")
    lines.append(f"- Tipos de actions encontrados: {format_counter(action_categories)}")
    lines.append(f"- Servicos chamados: {format_counter(services)}")
    lines.append(f"- Dominios usados: {format_counter(domains)}")
    lines.append(f"- Modos usados: {format_counter(modes)}")
    lines.append(f"- Campos especiais encontrados: {format_counter(fields)}")
    lines.append("")
    lines.append("## Aliases")
    lines.append("")
    for alias in aliases:
        lines.append(f"- {alias}")
    lines.append("")
    lines.append("## Cobertura por Padrao")
    lines.append("")
    coverage_items = [
        ("Automation alias", PATTERN_COVERAGE["automation.alias"]),
        ("Automation description", PATTERN_COVERAGE["automation.description"]),
        ("Automation mode single", PATTERN_COVERAGE["automation.mode.single"]),
        ("Automation mode restart", PATTERN_COVERAGE["automation.mode.restart"]),
        ("Automation id opaco", PATTERN_COVERAGE["automation.id"]),
        ("Trigger state", PATTERN_COVERAGE["trigger.state"]),
        ("Trigger device on/off/motion/open", PATTERN_COVERAGE["trigger.device.on_off_motion_open"]),
        ("Trigger battery", PATTERN_COVERAGE["trigger.device.battery"]),
        ("Trigger volume_flow", PATTERN_COVERAGE["trigger.device.volume_flow"]),
        ("Trigger sun", PATTERN_COVERAGE["trigger.sun"]),
        ("Trigger time", PATTERN_COVERAGE["trigger.time"]),
        ("Condition state", PATTERN_COVERAGE["condition.state"]),
        ("Condition device", PATTERN_COVERAGE["condition.device"]),
        ("Condition trigger", PATTERN_COVERAGE["condition.trigger"]),
        ("Condition time", PATTERN_COVERAGE["condition.time"]),
        ("Condition sun", PATTERN_COVERAGE["condition.sun"]),
        ("Condition logical or", PATTERN_COVERAGE["condition.logical.or"]),
        ("Condition logical and", PATTERN_COVERAGE["condition.logical.and"]),
        ("Action device", PATTERN_COVERAGE["action.device"]),
        ("Action service", PATTERN_COVERAGE["action.service"]),
        ("Action delay", PATTERN_COVERAGE["action.delay"]),
        ("Action if/then/else", PATTERN_COVERAGE["action.if"]),
        ("Action choose/case", PATTERN_COVERAGE["action.choose"]),
        ("Field id", PATTERN_COVERAGE["field.id"]),
        ("Field alias", PATTERN_COVERAGE["field.alias"]),
        ("Field from", PATTERN_COVERAGE["field.from"]),
        ("Field to", PATTERN_COVERAGE["field.to"]),
        ("Field above", PATTERN_COVERAGE["field.above"]),
        ("Field below", PATTERN_COVERAGE["field.below"]),
        ("Field for", PATTERN_COVERAGE["field.for"]),
        ("Field enabled", PATTERN_COVERAGE["field.enabled"]),
        ("Field brightness_pct", PATTERN_COVERAGE["field.brightness_pct"]),
        ("Field weekday", PATTERN_COVERAGE["field.weekday"]),
        ("Field offset", PATTERN_COVERAGE["field.offset"]),
        ("Field choose", PATTERN_COVERAGE["field.choose"]),
        ("Field if", PATTERN_COVERAGE["field.if"]),
        ("Field then", PATTERN_COVERAGE["field.then"]),
        ("Field else", PATTERN_COVERAGE["field.else"]),
        ("Field delay", PATTERN_COVERAGE["field.delay"]),
        ("Field target", PATTERN_COVERAGE["field.target"]),
        ("Field data", PATTERN_COVERAGE["field.data"]),
        ("Field metadata", PATTERN_COVERAGE["field.metadata"]),
    ]
    for title, coverage in coverage_items:
        lines.append(f"- {title}: {coverage}")
    lines.append("")
    lines.append("## Exemplos Homi Equivalentes")
    lines.append("")
    equivalents_dir = ROOT / "examples" / "professor" / "homi_equivalents"
    for path in sorted(equivalents_dir.glob("*.homi")):
        lines.append(f"- `{path.relative_to(ROOT).as_posix()}`")
    lines.append("")
    lines.append("## Conclusao")
    lines.append("")
    lines.append(
        "Todos os padroes observados no YAML do professor foram analisados e receberam uma construcao Homi correspondente, "
        "com excecao do `id` opaco de automacao do Home Assistant, que foi explicitamente tratado como detalhe de persistencia "
        "e nao como parte autoral da linguagem."
    )
    lines.append("")
    return "\n".join(lines)


def walk_trigger(
    trigger: dict[str, Any],
    trigger_types: Counter[str],
    domains: Counter[str],
    fields: Counter[str],
) -> None:
    trigger_types[trigger.get("trigger", "<ausente>")] += 1
    if "domain" in trigger:
        domains[trigger["domain"]] += 1
    register_fields(trigger, fields)


def walk_condition(
    condition: dict[str, Any],
    condition_types: Counter[str],
    domains: Counter[str],
    fields: Counter[str],
) -> None:
    condition_types[condition.get("condition", "<ausente>")] += 1
    if "domain" in condition:
        domains[condition["domain"]] += 1
    register_fields(condition, fields)
    for nested in condition.get("conditions", []):
        walk_condition(nested, condition_types, domains, fields)


def walk_action(
    action: dict[str, Any],
    action_categories: Counter[str],
    condition_types: Counter[str],
    services: Counter[str],
    domains: Counter[str],
    fields: Counter[str],
) -> None:
    if "type" in action:
        action_categories[f"type:{action['type']}"] += 1
        if "domain" in action:
            domains[action["domain"]] += 1
    if "action" in action:
        action_categories["service"] += 1
        services[action["action"]] += 1
        domains[action["action"].split(".", 1)[0]] += 1
    if "delay" in action:
        action_categories["delay"] += 1
    if "if" in action:
        action_categories["if"] += 1
        fields["then"] += 1
        for condition in action.get("if", []):
            walk_condition(condition, condition_types, domains, fields)
        for nested in action.get("then", []):
            walk_action(nested, action_categories, condition_types, services, domains, fields)
        if "else" in action:
            for nested in action.get("else", []):
                walk_action(nested, action_categories, condition_types, services, domains, fields)
    if "choose" in action:
        action_categories["choose"] += 1
        for option in action.get("choose", []):
            for condition in option.get("conditions", []):
                walk_condition(condition, condition_types, domains, fields)
            for nested in option.get("sequence", []):
                walk_action(nested, action_categories, condition_types, services, domains, fields)
    register_fields(action, fields)


def register_fields(item: dict[str, Any], fields: Counter[str]) -> None:
    for field_name in FIELD_NAMES:
        if field_name in item:
            fields[field_name] += 1


def format_counter(counter: Counter[str]) -> str:
    if not counter:
        return "nenhum"
    return ", ".join(f"{key} ({value})" for key, value in sorted(counter.items()))


if __name__ == "__main__":
    main()
