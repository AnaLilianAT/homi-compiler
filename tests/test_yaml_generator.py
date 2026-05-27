from pathlib import Path

import yaml

from src.ast_nodes import (
    Automation,
    ChooseAction,
    ChooseCase,
    DelayAction,
    DeviceAction,
    DeviceCondition,
    DeviceTrigger,
    Duration,
    IfAction,
    LiteralValue,
    LogicalCondition,
    ProgramNode,
    ServiceAction,
    StateCondition,
    StateTrigger,
    SunCondition,
    SunTrigger,
    TimeCondition,
    TimeTrigger,
    TriggerCondition,
)
from src.main import compile_file
from src.yaml_generator import generate_yaml


def test_yaml_generator_outputs_empty_automation_list() -> None:
    yaml_text = generate_yaml(ProgramNode())

    assert yaml.safe_load(yaml_text) == []


def test_yaml_generator_maps_automation_and_triggers() -> None:
    program = ProgramNode(
        automations=[
            Automation(
                alias="Nome",
                description="Descricao",
                mode="restart",
                triggers=[
                    StateTrigger(
                        entity_ids=["binary_sensor.a", "binary_sensor.b"],
                        to_states=[LiteralValue("on")],
                        trigger_id="Movimento",
                    ),
                    DeviceTrigger(
                        domain="switch",
                        device_id="abc",
                        entity_id="def",
                        device_type="ligado",
                        trigger_id="Liga",
                    ),
                    DeviceTrigger(
                        domain="sensor",
                        device_id="battery-device",
                        entity_id="sensor.bateria",
                        device_type="bateria",
                        below=LiteralValue(20),
                    ),
                    DeviceTrigger(
                        domain="sensor",
                        device_id="flow-device",
                        entity_id="sensor.fluxo",
                        device_type="volume_fluxo",
                        above=LiteralValue(3.5),
                    ),
                    SunTrigger(event="sunset", offset="-00:45:00", trigger_id="sol"),
                    TimeTrigger(at="05:00:00", trigger_id="Hora"),
                ],
            )
        ]
    )

    result = yaml.safe_load(generate_yaml(program))
    automation = result[0]

    assert automation["alias"] == "Nome"
    assert automation["description"] == "Descricao"
    assert automation["mode"] == "restart"
    assert automation["triggers"][0] == {
        "trigger": "state",
        "entity_id": ["binary_sensor.a", "binary_sensor.b"],
        "to": ["on"],
        "id": "Movimento",
    }
    assert automation["triggers"][1] == {
        "trigger": "device",
        "domain": "switch",
        "device_id": "abc",
        "entity_id": "def",
        "type": "turned_on",
        "id": "Liga",
    }
    assert automation["triggers"][2]["type"] == "battery_level"
    assert automation["triggers"][2]["below"] == 20
    assert automation["triggers"][3]["type"] == "volume_flow_rate"
    assert automation["triggers"][3]["above"] == 3.5
    assert automation["triggers"][4] == {
        "trigger": "sun",
        "event": "sunset",
        "offset": "-00:45:00",
        "id": "sol",
    }
    assert automation["triggers"][5] == {
        "trigger": "time",
        "at": "05:00:00",
        "id": "Hora",
    }


def test_yaml_generator_maps_conditions() -> None:
    program = ProgramNode(
        automations=[
            Automation(
                alias="Condicoes",
                conditions=[
                    StateCondition(
                        entity_id="switch.luzes_da_sala",
                        states=[LiteralValue("off")],
                    ),
                    DeviceCondition(
                        domain="switch",
                        device_id="abc",
                        entity_id="def",
                        condition_type="ligado",
                    ),
                    TriggerCondition(ids=["Movimento", "Liga"]),
                    TimeCondition(after="01:00:00", before="06:30:00", weekdays=["mon", "tue"]),
                    SunCondition(before="sunrise", after="sunset"),
                    LogicalCondition(
                        operator="or",
                        conditions=[
                            TriggerCondition(ids=["sol"]),
                            StateCondition(
                                entity_id="light.sala",
                                states=[LiteralValue("off")],
                            ),
                        ],
                    ),
                ],
            )
        ]
    )

    conditions = yaml.safe_load(generate_yaml(program))[0]["conditions"]

    assert conditions[0] == {
        "condition": "state",
        "entity_id": "switch.luzes_da_sala",
        "state": "off",
    }
    assert conditions[1] == {
        "condition": "device",
        "domain": "switch",
        "device_id": "abc",
        "entity_id": "def",
        "type": "is_on",
    }
    assert conditions[2] == {
        "condition": "trigger",
        "id": ["Movimento", "Liga"],
    }
    assert conditions[3] == {
        "condition": "time",
        "after": "01:00:00",
        "before": "06:30:00",
        "weekday": ["mon", "tue"],
    }
    assert conditions[4] == {
        "condition": "sun",
        "before": "sunrise",
        "after": "sunset",
    }
    assert conditions[5]["condition"] == "or"
    assert len(conditions[5]["conditions"]) == 2


def test_yaml_generator_maps_actions() -> None:
    program = ProgramNode(
        automations=[
            Automation(
                alias="Acoes",
                actions=[
                    DeviceAction(
                        domain="light",
                        device_id="abc",
                        entity_id="def",
                        action_type="ligar",
                        enabled=True,
                    ),
                    ServiceAction(
                        service="switch.turn_on",
                        target_entity_ids=["switch.a"],
                        target_device_ids=["dev-a", "dev-b"],
                        data={"message": "texto"},
                        enabled=False,
                    ),
                    DelayAction(duration=Duration("1min45s")),
                    IfAction(
                        conditions=[
                            TimeCondition(after="01:15:00", before="12:00:00")
                        ],
                        then_actions=[DelayAction(duration=Duration("45s"))],
                        else_actions=[DelayAction(duration=Duration("1min45s"))],
                    ),
                    ChooseAction(
                        cases=[
                            ChooseCase(
                                conditions=[TriggerCondition(ids=["sol"])],
                                sequence=[
                                    ServiceAction(
                                        service="automation.trigger",
                                        target_entity_ids=["automation.cozinha_ligar_luzes"],
                                        data={"skip_condition": True},
                                    )
                                ],
                            )
                        ]
                    ),
                ],
            )
        ]
    )

    actions = yaml.safe_load(generate_yaml(program))[0]["actions"]

    assert actions[0] == {
        "type": "turn_on",
        "device_id": "abc",
        "entity_id": "def",
        "domain": "light",
        "enabled": True,
    }
    assert actions[1] == {
        "action": "switch.turn_on",
        "target": {
            "entity_id": ["switch.a"],
            "device_id": ["dev-a", "dev-b"],
        },
        "data": {"message": "texto"},
        "enabled": False,
    }
    assert actions[2] == {
        "delay": {
            "hours": 0,
            "minutes": 1,
            "seconds": 45,
            "milliseconds": 0,
        }
    }
    assert actions[3] == {
        "if": [
            {
                "condition": "time",
                "after": "01:15:00",
                "before": "12:00:00",
            }
        ],
        "then": [
            {
                "delay": {
                    "hours": 0,
                    "minutes": 0,
                    "seconds": 45,
                    "milliseconds": 0,
                }
            }
        ],
        "else": [
            {
                "delay": {
                    "hours": 0,
                    "minutes": 1,
                    "seconds": 45,
                    "milliseconds": 0,
                }
            }
        ],
    }
    assert actions[4] == {
        "choose": [
            {
                "conditions": [{"condition": "trigger", "id": "sol"}],
                "sequence": [
                    {
                        "action": "automation.trigger",
                        "target": {
                            "entity_id": ["automation.cozinha_ligar_luzes"],
                        },
                        "data": {"skip_condition": True},
                    }
                ],
            }
        ]
    }


def test_yaml_generator_validates_yaml_output() -> None:
    program = ProgramNode(
        automations=[
            Automation(
                alias="Unicode",
                description="Áudio na sala",
                mode="single",
                actions=[
                    ServiceAction(
                        service="tts.speak",
                        target_entity_ids=["media_player.sala"],
                        data={"message": "Olá, mundo"},
                    )
                ],
            )
        ]
    )

    parsed = yaml.safe_load(generate_yaml(program))

    assert parsed[0]["description"] == "Áudio na sala"
    assert parsed[0]["actions"][0]["data"]["message"] == "Olá, mundo"


def test_cli_compiles_minimal_example(tmp_path: Path) -> None:
    source_path = tmp_path / "minimal.homi"
    output_path = tmp_path / "minimal.yaml"
    source_path.write_text("", encoding="utf-8")

    exit_code = compile_file(source_path, output_path)

    assert exit_code == 0
    assert yaml.safe_load(output_path.read_text(encoding="utf-8")) == []
