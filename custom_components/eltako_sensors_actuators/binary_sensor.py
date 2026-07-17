from __future__ import annotations

import logging
from typing import Any

from homeassistant.helpers.event import async_call_later

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity

from .const import CONF_DEVICES, DOMAIN
from .entity_base import EltakoBaseEntity, EltakoGatewayEntity, EltakoYamlEntity, normalize_eep, normalize_platform

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    data = {**entry.data, **entry.options}
    gateway = hass.data[DOMAIN][entry.entry_id]
    devices = data.get(CONF_DEVICES) or []

    entities: list[BinarySensorEntity] = _gateway_binary_entities(gateway)

    for device in devices:
        if not isinstance(device, dict):
            continue
        platform = normalize_platform(device.get("platform"))
        eep = normalize_eep(device.get("eep"))

        if eep in ("A5-07-01", "A5-08-01") and platform in ("sensor", "binary_sensor"):
            # FBH/FBHT uses one telegram for the physical movement state in both
            # FBH mode (A5-08-01) and TF mode (A5-07-01). Do not route these
            # profiles through the generic binary-sensor key "pressed".
            entities.append(EltakoYamlBinarySensor(gateway, device, "movement", BinarySensorDeviceClass.MOTION, suffix="Bewegung"))
        elif platform == "binary_sensor":
            device_class = _device_class_from_yaml(device.get("device_class")) or _device_class_for_eep(eep)
            key = "open" if device_class in (BinarySensorDeviceClass.DOOR, BinarySensorDeviceClass.WINDOW, BinarySensorDeviceClass.OPENING) else "pressed"
            entities.append(EltakoYamlBinarySensor(gateway, device, key, device_class))
            if eep in ("F6-02-01", "F6-02-02"):
                entities.extend(_rocker_position_entities(gateway, device))
        elif platform == "sensor" and eep == "A5-13-01":
            entities.append(EltakoYamlBinarySensor(gateway, device, "rain", BinarySensorDeviceClass.MOISTURE, suffix="Regen"))
        elif eep == "A5-20-01":
            entities.extend(_a5_20_01_status_entities(gateway, device))

    if not devices and not entities:
        entities.extend(
            [
                EltakoBinaryValueSensor(gateway, "debug", "Last Movement", "movement", BinarySensorDeviceClass.MOTION),
                EltakoBinaryValueSensor(gateway, "debug", "Last Contact", "open", BinarySensorDeviceClass.DOOR),
            ]
        )

    _LOGGER.info(
        "ELTAKO binary_sensor setup entry=%s imported_devices=%s binary_entities=%s",
        entry.entry_id,
        len(devices) if isinstance(devices, list) else 0,
        len(entities),
    )
    async_add_entities(entities)



def _a5_20_01_status_entities(gateway, device: dict[str, Any]) -> list[BinarySensorEntity]:
    return [
        EltakoYamlBinarySensor(gateway, device, "battery_low", BinarySensorDeviceClass.BATTERY, suffix="Batterie niedrig"),
        EltakoYamlBinarySensor(gateway, device, "window_open", BinarySensorDeviceClass.WINDOW, suffix="Fenster offen"),
        EltakoYamlBinarySensor(gateway, device, "contact_open", BinarySensorDeviceClass.OPENING, suffix="Kontakt offen"),
        EltakoYamlBinarySensor(gateway, device, "actuator_obstructed", BinarySensorDeviceClass.PROBLEM, suffix="Ventil blockiert"),
        EltakoYamlBinarySensor(gateway, device, "temperature_sensor_failure", BinarySensorDeviceClass.PROBLEM, suffix="Temperaturfehler"),
    ]

def _gateway_binary_entities(gateway) -> list[BinarySensorEntity]:
    return [
        EltakoGatewayBinarySensor(gateway, "Connected", "connected", BinarySensorDeviceClass.CONNECTIVITY),
        EltakoGatewayBinarySensor(gateway, "Auto Connect Enabled", "auto_connect_enabled", None),
    ]


class EltakoGatewayBinarySensor(EltakoGatewayEntity, BinarySensorEntity):
    def __init__(self, gateway, name: str, key: str, device_class: BinarySensorDeviceClass | None) -> None:
        super().__init__(gateway, name, key)
        self.key = key
        self._attr_device_class = device_class
        self._remove_listener = gateway.register_listener(self._handle_telegram)

    @property
    def is_on(self):
        if self.key == "connected":
            return self.gateway.is_connected
        if self.key == "auto_connect_enabled":
            return bool(getattr(self.gateway, "auto_connect_enabled", True))
        return None

    def _handle_telegram(self, telegram) -> None:
        self.schedule_update_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        if self._remove_listener:
            self._remove_listener()



ROCKER_POSITION_LABELS = {
    "left_top": "Taste oben links",
    "right_top": "Taste oben rechts",
    "left_bottom": "Taste unten links",
    "right_bottom": "Taste unten rechts",
}

ROCKER_ACTIVE_TIME_SECONDS = 0.7


def _rocker_position_entities(gateway, device: dict[str, Any]) -> list[BinarySensorEntity]:
    return [
        EltakoRockerPositionBinarySensor(gateway, device, position, label)
        for position, label in ROCKER_POSITION_LABELS.items()
    ]

def _device_class_from_yaml(value: Any) -> BinarySensorDeviceClass | None:
    """Return a Home Assistant binary-sensor device class from YAML.

    EEDTOY can export device_class for manually added devices.  Prefer the
    explicit YAML value over the EEP fallback so FTK/FTKE can be window/door
    as selected and special profiles such as FSM60B BA3 can be moisture.
    """
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    try:
        return BinarySensorDeviceClass(text)
    except ValueError:
        return getattr(BinarySensorDeviceClass, text.upper(), None)


def _device_class_for_eep(eep: str) -> BinarySensorDeviceClass | None:
    if eep == "F6-10-00":
        return BinarySensorDeviceClass.DOOR
    if eep == "D5-00-01":
        return BinarySensorDeviceClass.DOOR
    if eep in ("F6-02-01", "F6-02-02"):
        return None
    return None


class EltakoYamlBinarySensor(EltakoYamlEntity, BinarySensorEntity):
    def __init__(
        self,
        gateway,
        device: dict[str, Any],
        key: str,
        device_class: BinarySensorDeviceClass | None,
        suffix: str | None = None,
    ) -> None:
        super().__init__(gateway, device, suffix=suffix)
        self.key = key
        self._state = None
        self._attr_device_class = device_class
        self._remove_listener = gateway.register_listener(self._handle_telegram)

    @property
    def is_on(self):
        return self._state

    def _handle_telegram(self, telegram) -> None:
        if str(telegram.sender_id).upper() != str(self.device_config.get("id")).upper():
            return
        if self.key not in telegram.decoded:
            return
        self._state = bool(telegram.decoded[self.key])
        self.schedule_update_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        if self._remove_listener:
            self._remove_listener()


class EltakoBinaryValueSensor(EltakoBaseEntity, BinarySensorEntity):
    def __init__(self, gateway, sender_id: str, name: str, key: str, device_class: BinarySensorDeviceClass | None) -> None:
        super().__init__(gateway, sender_id, name)
        self.key = key
        self._state = None
        self._attr_device_class = device_class
        self._remove_listener = gateway.register_listener(self._handle_telegram)

    @property
    def is_on(self):
        return self._state

    def _handle_telegram(self, telegram) -> None:
        if self.key not in telegram.decoded:
            return
        self._state = bool(telegram.decoded[self.key])
        self.schedule_update_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        if self._remove_listener:
            self._remove_listener()


class EltakoRockerPositionBinarySensor(EltakoYamlEntity, BinarySensorEntity):
    """Momentary binary sensor for one physical position of an Eltako rocker button."""

    def __init__(self, gateway, device: dict[str, Any], position: str, label: str) -> None:
        super().__init__(gateway, device, suffix=label)
        self.position = position
        self._state = False
        self._reset_handle = None
        self._attr_device_class = None
        self._attr_icon = "mdi:gesture-tap-button"
        self._remove_listener = gateway.register_listener(self._handle_telegram)

    @property
    def is_on(self):
        return self._state

    def _handle_telegram(self, telegram) -> None:
        if str(telegram.sender_id).upper() != str(self.device_config.get("id")).upper():
            return

        position = telegram.decoded.get("button_position")
        if not position:
            return

        if position == self.position and bool(telegram.decoded.get("pressed", False)):
            self._state = True
            self.schedule_update_ha_state()
            self._schedule_reset()
            return

        # A different button on the same rocker was pressed. Clear this one
        # immediately so the visual state is unambiguous.
        if position in ROCKER_POSITION_LABELS and self._state:
            self._cancel_reset()
            self._state = False
            self.schedule_update_ha_state()

    def _schedule_reset(self) -> None:
        self._cancel_reset()

        def _reset(_now) -> None:
            self._reset_handle = None
            if self._state:
                self._state = False
                self.schedule_update_ha_state()

        self._reset_handle = async_call_later(self.hass, ROCKER_ACTIVE_TIME_SECONDS, _reset)

    def _cancel_reset(self) -> None:
        if self._reset_handle is not None:
            self._reset_handle()
            self._reset_handle = None

    async def async_will_remove_from_hass(self) -> None:
        self._cancel_reset()
        if self._remove_listener:
            self._remove_listener()
