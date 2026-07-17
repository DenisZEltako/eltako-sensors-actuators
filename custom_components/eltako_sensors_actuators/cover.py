from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.cover import CoverEntity
from homeassistant.exceptions import HomeAssistantError

try:
    from homeassistant.components.cover import CoverEntityFeature
    _SUPPORT_OPEN = CoverEntityFeature.OPEN
    _SUPPORT_CLOSE = CoverEntityFeature.CLOSE
    _SUPPORT_STOP = CoverEntityFeature.STOP
except Exception:  # pragma: no cover - older HA compatibility
    _SUPPORT_OPEN = 1
    _SUPPORT_CLOSE = 2
    _SUPPORT_STOP = 8

from .const import CONF_DEVICES, DOMAIN
from .entity_base import EltakoYamlEntity, normalize_platform

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    data = {**entry.data, **entry.options}
    gateway = hass.data[DOMAIN][entry.entry_id]
    devices = data.get(CONF_DEVICES) or []
    entities = [
        EltakoCover(gateway, device)
        for device in devices
        if isinstance(device, dict) and normalize_platform(device.get("platform")) == "cover"
    ]
    _LOGGER.info(
        "ELTAKO cover setup entry=%s imported_devices=%s cover_entities=%s",
        entry.entry_id,
        len(devices) if isinstance(devices, list) else 0,
        len(entities),
    )
    async_add_entities(entities)


class EltakoCover(EltakoYamlEntity, CoverEntity):
    _attr_supported_features = _SUPPORT_OPEN | _SUPPORT_CLOSE | _SUPPORT_STOP

    def __init__(self, gateway, device: dict[str, Any]) -> None:
        super().__init__(gateway, device)
        self._is_closed = None
        self._position = None
        self._remove_listener = gateway.register_listener(self._handle_telegram)

    @property
    def is_closed(self):
        return self._is_closed

    @property
    def current_cover_position(self):
        return self._position

    def _handle_telegram(self, telegram) -> None:
        if str(telegram.sender_id).upper() not in {
            str(self.device_config.get("id")).upper(),
            str(self.device_config.get("sender_id")).upper(),
        }:
            return
        if "position" in telegram.decoded:
            self._position = telegram.decoded["position"]
        if "closed" in telegram.decoded:
            self._is_closed = bool(telegram.decoded["closed"])
        self.schedule_update_ha_state()

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self._async_send_or_raise("open")

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self._async_send_or_raise("close")

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self._async_send_or_raise("stop")

    async def _async_send_or_raise(self, command: str) -> None:
        ok = await self.gateway.async_send_actuator_command(self.device_config, command)
        if not ok:
            detail = getattr(self.gateway, "last_send_error", None)
            suffix = f" Technischer Fehler: {detail}" if detail else ""
            raise HomeAssistantError(
                "ELTAKO Telegramm konnte nicht gesendet werden. Pruefe Gateway-Port, sender.id/sender.eep im YAML und ob der Aktor die Sender-ID angelernt hat."
                + suffix
            )
        if command == "open":
            self._is_closed = False
        elif command == "close":
            self._is_closed = True
        self.schedule_update_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        if self._remove_listener:
            self._remove_listener()
