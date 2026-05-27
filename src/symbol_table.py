from __future__ import annotations

from dataclasses import dataclass, field

from .ast_nodes import DeviceDeclaration, EntityDeclaration, infer_domain_from_dotted_name


VALID_DOMAINS = {
    "light",
    "switch",
    "sensor",
    "binary_sensor",
    "alarm_control_panel",
    "timer",
    "media_player",
    "automation",
    "notify",
    "cover",
    "weather",
    "tts",
    "alexa_devices",
}


@dataclass(slots=True)
class EntitySymbol:
    name: str
    entity_id: str
    domain: str


@dataclass(slots=True)
class DeviceSymbol:
    name: str
    domain: str
    device_id: str
    entity_id: str


@dataclass(slots=True)
class ResolvedEntity:
    entity_id: str
    domain: str
    symbolic: bool


@dataclass(slots=True)
class ResolvedDevice:
    domain: str
    device_id: str
    entity_id: str
    symbolic: bool


@dataclass(slots=True)
class SymbolTable:
    entities: dict[str, EntitySymbol] = field(default_factory=dict)
    devices: dict[str, DeviceSymbol] = field(default_factory=dict)

    def define_entity(self, declaration: EntityDeclaration) -> EntitySymbol:
        domain = declaration.domain or infer_domain_from_dotted_name(declaration.entity_id) or ""
        symbol = EntitySymbol(
            name=declaration.name,
            entity_id=declaration.entity_id,
            domain=domain,
        )
        self.entities[declaration.name] = symbol
        return symbol

    def define_device(self, declaration: DeviceDeclaration) -> DeviceSymbol:
        symbol = DeviceSymbol(
            name=declaration.name,
            domain=declaration.domain,
            device_id=declaration.device_id,
            entity_id=declaration.entity_id,
        )
        self.devices[declaration.name] = symbol
        return symbol

    def lookup_entity(self, name: str) -> EntitySymbol | None:
        return self.entities.get(name)

    def lookup_device(self, name: str) -> DeviceSymbol | None:
        return self.devices.get(name)

    def resolve_entity_reference(self, name: str) -> ResolvedEntity | None:
        if "." in name:
            domain = infer_domain_from_dotted_name(name)
            if domain is None:
                return None
            return ResolvedEntity(entity_id=name, domain=domain, symbolic=False)

        entity_symbol = self.lookup_entity(name)
        if entity_symbol is not None:
            return ResolvedEntity(
                entity_id=entity_symbol.entity_id,
                domain=entity_symbol.domain,
                symbolic=True,
            )

        device_symbol = self.lookup_device(name)
        if device_symbol is not None:
            return ResolvedEntity(
                entity_id=device_symbol.entity_id,
                domain=device_symbol.domain,
                symbolic=True,
            )

        return None

    def resolve_device_reference(
        self,
        domain_or_name: str,
        device_id: str | None,
        entity_id: str | None,
    ) -> ResolvedDevice | None:
        if device_id and entity_id:
            return ResolvedDevice(
                domain=domain_or_name,
                device_id=device_id,
                entity_id=entity_id,
                symbolic=False,
            )

        symbol = self.lookup_device(domain_or_name)
        if symbol is None:
            return None

        return ResolvedDevice(
            domain=symbol.domain,
            device_id=symbol.device_id,
            entity_id=symbol.entity_id,
            symbolic=True,
        )

    def to_debug_dict(self) -> dict[str, list[dict[str, str]]]:
        return {
            "entities": [
                {
                    "name": symbol.name,
                    "entity_id": symbol.entity_id,
                    "domain": symbol.domain,
                }
                for symbol in self.entities.values()
            ],
            "devices": [
                {
                    "name": symbol.name,
                    "domain": symbol.domain,
                    "device_id": symbol.device_id,
                    "entity_id": symbol.entity_id,
                }
                for symbol in self.devices.values()
            ],
        }
