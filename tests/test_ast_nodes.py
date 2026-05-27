from src.ast_nodes import (
    Automation,
    ChooseAction,
    ChooseCase,
    DelayAction,
    DeviceAction,
    DeviceCondition,
    DeviceDeclaration,
    DeviceTrigger,
    Duration,
    EntityDeclaration,
    IfAction,
    LiteralValue,
    LogicalCondition,
    Program,
    ServiceAction,
    StateCondition,
    StateTrigger,
    SunTrigger,
    TimeCondition,
    TimeTrigger,
    TriggerCondition,
)


def test_entity_declaration_infers_domain_from_entity_id() -> None:
    entity = EntityDeclaration(name="luz_sala", entity_id="light.sala")

    assert entity.domain == "light"


def test_program_can_hold_declarations_and_automations() -> None:
    program = Program(
        declarations=[
            EntityDeclaration(name="luz_sala", entity_id="light.sala"),
            DeviceDeclaration(
                name="painel_tv",
                domain="switch",
                device_id="dev-123",
                entity_id="switch.painel_tv",
            ),
        ],
        automations=[
            Automation(
                alias="Sala - movimento",
                description="Liga a luz",
                mode="restart",
                triggers=[
                    StateTrigger(
                        entity_ids=["binary_sensor.movimento_sala"],
                        to_states=[LiteralValue("on")],
                        trigger_id="Movimento",
                    ),
                    DeviceTrigger(
                        domain="sensor",
                        device_id="dev-sensor",
                        entity_id="sensor.tablet_bateria",
                        device_type="bateria",
                        below=LiteralValue(20),
                    ),
                    SunTrigger(event="sunset", offset="-00:45:00", trigger_id="sol"),
                    TimeTrigger(at="05:00:00", trigger_id="Hora"),
                ],
                conditions=[
                    StateCondition(
                        entity_id="switch.luzes_da_sala",
                        states=[LiteralValue("off")],
                    ),
                    DeviceCondition(
                        domain="switch",
                        device_id="dev-switch",
                        entity_id="switch.luzes_da_sala",
                        condition_type="is_on",
                    ),
                    TriggerCondition(ids=["Movimento", "Hora"]),
                    TimeCondition(after="01:00:00", before="06:30:00"),
                    LogicalCondition(
                        operator="or",
                        conditions=[
                            TriggerCondition(ids=["sol"]),
                            StateCondition(
                                entity_id="weather.forecast_casa",
                                states=[LiteralValue("rainy")],
                            ),
                        ],
                    ),
                ],
                actions=[
                    DeviceAction(
                        domain="light",
                        device_id="dev-light",
                        entity_id="light.sala",
                        action_type="turn_on",
                        brightness_pct=80,
                        enabled=True,
                    ),
                    ServiceAction(
                        service="notify.mobile_app_zfold4",
                        target_entity_ids=["notify.mobile_app_zfold4"],
                        data={"message": "Sala ligada"},
                    ),
                    DelayAction(duration=Duration("45s")),
                    IfAction(
                        conditions=[TriggerCondition(ids=["Movimento"])],
                        then_actions=[
                            ServiceAction(
                                service="timer.start",
                                target_entity_ids=["timer.sala"],
                            )
                        ],
                        else_actions=[
                            ServiceAction(
                                service="timer.finish",
                                target_entity_ids=["timer.sala"],
                            )
                        ],
                    ),
                    ChooseAction(
                        cases=[
                            ChooseCase(
                                conditions=[
                                    StateCondition(
                                        entity_id="weather.forecast_casa",
                                        states=[LiteralValue("rainy")],
                                    )
                                ],
                                sequence=[
                                    ServiceAction(
                                        service="automation.trigger",
                                        target_entity_ids=[
                                            "automation.cozinha_ligar_luzes"
                                        ],
                                        data={"skip_condition": True},
                                    )
                                ],
                            )
                        ]
                    ),
                ],
            )
        ],
    )

    assert len(program.declarations) == 2
    assert len(program.automations) == 1
    assert program.automations[0].alias == "Sala - movimento"
    assert program.automations[0].name == "Sala - movimento"


def test_ast_debug_string_is_useful() -> None:
    action = ServiceAction(
        service="media_player.volume_set",
        target_entity_ids=["media_player.sala"],
        data={"volume_level": 0.5},
        enabled=True,
    )

    text = repr(action)

    assert "ServiceAction" in text
    assert "media_player.volume_set" in text
    assert "volume_level" in text
