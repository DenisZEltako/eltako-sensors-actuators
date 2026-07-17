from __future__ import annotations

from .esp2 import ESP2Message, build_regular_4bs
from .ids import parse_address

COMMAND_STOP = 0x00
COMMAND_OPEN = 0x01
COMMAND_CLOSE = 0x02


def build_h5_3f_7f_cover(sender_id: str, command: str, duration_seconds: int = 255) -> ESP2Message:
    """Build H5-3F-7F cover command for ELTAKO Series-14 covers."""
    address = parse_address(sender_id)
    normalized = command.lower().strip()
    if normalized == "open":
        command_byte = COMMAND_OPEN
    elif normalized == "close":
        command_byte = COMMAND_CLOSE
    elif normalized == "stop":
        command_byte = COMMAND_STOP
    else:
        raise ValueError(f"Unsupported cover command: {command!r}")

    duration = 0 if command_byte == COMMAND_STOP else max(1, min(255, int(duration_seconds)))
    data = bytes([0x00, duration, command_byte, 0x08])
    return build_regular_4bs(address, data, status=0x00, outgoing=True)
