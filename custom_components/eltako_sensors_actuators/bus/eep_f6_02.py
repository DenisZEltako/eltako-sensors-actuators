from __future__ import annotations

from .esp2 import ESP2Message, build_rps
from .ids import parse_address


def build_f6_02_01_rocker(sender_id: str, action: int, pressed: bool = True, status: int | None = None) -> ESP2Message:
    """Build a simple F6-02-01 rocker telegram.

    This is provided for future use and diagnostics. It is not the preferred
    Series-14 actuator control path when A5-38-08 sender data is available.
    """
    address = parse_address(sender_id)
    data_byte = ((int(action) & 0x07) << 5) | (0x10 if pressed else 0x00)
    if status is None:
        status = 0x30 if pressed else 0x20
    return build_rps(address, data_byte, status=status, outgoing=True)
