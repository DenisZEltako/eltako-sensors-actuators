from __future__ import annotations

from .esp2 import ESP2Message, build_regular_4bs
from .ids import parse_address


def _temp_to_byte(value: float | int | None, default: float = 20.0) -> int:
    try:
        temperature = float(value)
    except (TypeError, ValueError):
        temperature = default
    temperature = max(0.0, min(40.0, temperature))
    return max(0, min(255, int(round(temperature / 40.0 * 255.0))))


def _ftr_fhk_mode_to_status_byte(hvac_mode: str | None) -> int:
    """Return the A5-10-06 FTR/FHK status byte (DB0).

    The ELTAKO FTR55ESB/FTR55EHB documentation for operating mode FHK lists
    the runtime bytes as:
      DB2 = target temperature 0..40 C
      DB1 = current temperature 0..40 C, inverted 255..0
      DB0 = 0x0F

    Earlier versions used the generic HeatingCooling priority byte (0x0E/0x08)
    and DB3 mode byte (0x70). FHK14 did not accept that. For the FHK/FTR
    compatible sender profile we emulate the documented room-controller
    telegram: DB3=0x00 and DB0=0x0F for heat/normal operation. For off we use
    DB0=0x00 only as a conservative fallback.
    """
    mode = str(hvac_mode or "heat").strip().lower()
    if mode in ("off", "aus", "false", "0"):
        return 0x00
    return 0x0F


def build_a5_10_06_room_control(
    sender_id: str,
    *,
    target_temperature: float | int | None = None,
    current_temperature: float | int | None = None,
    hvac_mode: str | None = "heat",
    priority: str | int | None = None,
) -> ESP2Message:
    """Build an ELTAKO FTR/FHK-compatible A5-10-06 runtime telegram.

    FHK14 is taught in as a virtual FTR/FTR55ESB style room controller. The
    documented FHK runtime telegram does not use DB3 as a HeatingCooling mode
    byte. It uses DB2 target temperature, DB1 inverted current temperature and
    DB0 fixed to 0x0F.
    """
    address = parse_address(sender_id)
    target_byte = _temp_to_byte(target_temperature, default=20.0)
    if current_temperature is None:
        current_temperature = target_temperature if target_temperature is not None else 20.0
    current_byte = 255 - _temp_to_byte(current_temperature, default=20.0)
    status_byte = _ftr_fhk_mode_to_status_byte(hvac_mode)

    data = bytes([0x00, target_byte, current_byte, status_byte])
    return build_regular_4bs(address, data, status=0x80, outgoing=True)
