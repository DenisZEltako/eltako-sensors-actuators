from __future__ import annotations

from typing import Any

from homeassistant.helpers.entity import DeviceInfo, Entity

from .const import DOMAIN


def normalize_platform(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_")


def normalize_eep(value: Any) -> str:
    return str(value or "").strip().upper()


def device_key(device: dict[str, Any]) -> str:
    gateway = device.get("gateway") if isinstance(device.get("gateway"), dict) else {}
    gateway_id = gateway.get("id") or gateway.get("device_type") or "gateway"
    return (
        f"{gateway_id}_{normalize_platform(device.get('platform'))}_{device.get('id')}_{device.get('eep')}"
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
    )


def gateway_device_name(gateway) -> str:
    """Return the Home Assistant device name for the configured ELTAKO gateway."""
    info = getattr(gateway, "selected_gateway", None) or {}
    if not isinstance(info, dict):
        info = {}

    gateway_id = info.get("id")
    device_type = str(info.get("device_type") or getattr(gateway, "gateway_type", None) or "gateway").lower()
    base_id = info.get("base_id") or getattr(gateway, "base_id", None)

    label = f"EnOcean Gateway - {device_type}"
    details = []
    if gateway_id is not None and str(gateway_id).strip():
        details.append(f"Id: {gateway_id}")
    if base_id:
        details.append(f"BaseId: {base_id}")
    if details:
        label += f" ({', '.join(details)})"
    return label


def gateway_model(gateway) -> str:
    info = getattr(gateway, "selected_gateway", None) or {}
    if not isinstance(info, dict):
        info = {}
    device_type = str(info.get("device_type") or getattr(gateway, "gateway_type", None) or "Gateway").upper()
    return f"EnOcean Gateway - {device_type}"


def _id_with_offset(device_id: Any, offset: int) -> str | None:
    text = str(device_id or "").strip().upper()
    parts = text.split("-")
    if len(parts) != 4:
        return None
    try:
        value = int("".join(parts), 16) + int(offset)
    except ValueError:
        return None
    if not 0 <= value <= 0xFFFFFFFF:
        return None
    return "-".join(f"{(value >> shift) & 0xFF:02X}" for shift in (24, 16, 8, 0))


def _strip_flgtf_suffix(name: str) -> str:
    import re

    text = str(name or "FLGTF").strip()
    text = re.sub(r"\s+(TVOC|LUFTGÜTE|LUFTGUETE|TEMPERATUR\s*\+?\s*FEUCHTE|TEMPERATUR|FEUCHTE)$", "", text, flags=re.IGNORECASE)
    return text.strip() or "FLGTF"


def _is_flgtf_device(device: dict[str, Any]) -> bool:
    if not isinstance(device, dict):
        return False
    eep = normalize_eep(device.get("eep"))
    raw = device.get("raw") if isinstance(device.get("raw"), dict) else {}
    text = " ".join(
        str(value or "")
        for value in (
            device.get("name"),
            device.get("device_type"),
            device.get("model"),
            device.get("eltako"),
            raw.get("name"),
            raw.get("device_type"),
            raw.get("model"),
            raw.get("eltako"),
        )
    ).upper()
    return "FLGTF" in text and eep in ("A5-09-0C", "A5-04-02")


def _flgtf_device_base_id(device: dict[str, Any]) -> str:
    device_id = str(device.get("id") or "").upper()
    eep = normalize_eep(device.get("eep"))
    if eep == "A5-04-02":
        return _id_with_offset(device_id, -1) or device_id
    return device_id


class EltakoGatewayEntity(Entity):
    """Base entity attached directly to the configured ELTAKO gateway device."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_available = True

    def __init__(self, gateway, name: str, unique_suffix: str) -> None:
        self.gateway = gateway
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_{gateway.entry_id}_gateway_{unique_suffix}".lower()

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.gateway.entry_id)},
            manufacturer="ELTAKO",
            name=gateway_device_name(self.gateway),
            model=gateway_model(self.gateway),
        )


class EltakoBaseEntity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_available = True

    def __init__(self, gateway, sender_id: str, name: str, device: dict[str, Any] | None = None) -> None:
        self.gateway = gateway
        self.device_config = device or {}
        self.sender_id = str(sender_id).upper()
        self._attr_name = name
        self._attr_unique_id = (
            f"{DOMAIN}_{gateway.entry_id}_{self.sender_id}_{name}".lower().replace(" ", "_").replace("/", "_")
        )

    @property
    def device_info(self) -> DeviceInfo:
        if self.device_config:
            gateway_info = self.device_config.get("gateway") if isinstance(self.device_config.get("gateway"), dict) else {}
            device_id = str(self.device_config.get("id") or self.sender_id).upper()
            name = str(self.device_config.get("name") or f"ELTAKO {device_id}")
            eep = self.device_config.get("eep")
            model = f"EEP {eep}" if eep else "ELTAKO Device"

            # FLGTF sends TVOC and temperature/humidity as two EnOcean IDs
            # (A5-09-0C and A5-04-02, usually ID + 1).  In Home Assistant this
            # must still be one physical device, just like a combined CO2/temp/
            # humidity sensor.  Group both IDs under the TVOC/base ID.
            if _is_flgtf_device(self.device_config):
                base_id = _flgtf_device_base_id(self.device_config)
                if base_id:
                    device_id = f"FLGTF_{base_id}"
                name = _strip_flgtf_suffix(name)
                model = "FLGTF (A5-09-0C + A5-04-02)"

            return DeviceInfo(
                identifiers={(DOMAIN, self.gateway.entry_id, device_id)},
                manufacturer="ELTAKO",
                name=name,
                model=model,
                via_device=(DOMAIN, self.gateway.entry_id),
            )

        return DeviceInfo(
            identifiers={(DOMAIN, self.sender_id)},
            manufacturer="ELTAKO",
            name=f"ELTAKO {self.sender_id}",
            via_device=(DOMAIN, self.gateway.entry_id),
        )


class EltakoYamlEntity(EltakoBaseEntity):
    """Base class for entities created from pasted/imported EEDTOY YAML."""

    def __init__(self, gateway, device: dict[str, Any], name: str | None = None, suffix: str | None = None) -> None:
        entity_name = name or str(device.get("name") or device.get("id") or "ELTAKO Device")
        if suffix:
            # With has_entity_name=True Home Assistant already prefixes the
            # entity with the physical device name.  FLGTF YAML historically
            # contained names such as "FLGTF TVOC" and the generic code added
            # the suffix once more, producing names/object IDs like
            # "FLGTF TVOC TVOC" / sensor.flgtf_flgtf_tvoc_tvoc.
            # Keep the physical device name in DeviceInfo and use only the
            # functional entity name for the three primary FLGTF values.
            if _is_flgtf_device(device) and suffix.casefold() in {
                "tvoc",
                "temperatur",
                "luftfeuchtigkeit",
            }:
                entity_name = suffix
            else:
                entity_name = f"{entity_name} {suffix}"
        sender_id = str(device.get("id") or device.get("sender_id") or entity_name)
        super().__init__(gateway, sender_id, entity_name, device)
        base = device_key(device)
        if suffix:
            base = f"{base}_{suffix}".lower().replace(" ", "_").replace("/", "_")
        self._attr_unique_id = f"{DOMAIN}_{gateway.entry_id}_{base}"
        self._attr_extra_state_attributes = {
            "eltako_id": device.get("id"),
            "eep": device.get("eep"),
            "sender_id": device.get("sender_id"),
            "sender_eep": device.get("sender_eep"),
            "platform": device.get("platform"),
            "gateway": device.get("gateway"),
        }
