from __future__ import annotations

from .esp2 import ESP2Message, build_regular_4bs
from .ids import parse_address


def build_a5_38_08_switch(sender_id: str, state: bool, time_seconds: float = 0.0) -> ESP2Message:
    """Build EEP A5-38-08 central switching command.

    Data bytes follow the central command layout:
    DB3 command=0x01, DB2/DB1 time*10, DB0 flags:
    learn button=1 and switching command bit = state.
    """
    address = parse_address(sender_id)
    ticks = max(0, min(0xFFFF, int(round(time_seconds * 10.0))))
    data = bytes([
        0x01,
        (ticks >> 8) & 0xFF,
        ticks & 0xFF,
        0x08 | (0x01 if state else 0x00),
    ])
    return build_regular_4bs(address, data, status=0x00, outgoing=True)


def build_a5_38_08_dimming(sender_id: str, brightness_percent: int, ramping_time: int = 0, state: bool | None = None) -> ESP2Message:
    """Build EEP A5-38-08 central dimming command."""
    address = parse_address(sender_id)
    value = max(0, min(100, int(brightness_percent)))
    switch_bit = 1 if (state if state is not None else value > 0) else 0
    data = bytes([
        0x02,
        value & 0xFF,
        max(0, min(255, int(ramping_time))) & 0xFF,
        0x08 | switch_bit,
    ])
    return build_regular_4bs(address, data, status=0x00, outgoing=True)
