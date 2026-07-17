from __future__ import annotations

import re

from .exceptions import InvalidAddressError

_ADDR_RE = re.compile(r"^[0-9A-Fa-f]{2}([-:])[0-9A-Fa-f]{2}\1[0-9A-Fa-f]{2}\1[0-9A-Fa-f]{2}$")


def parse_address(value: str | bytes | bytearray | list[int] | tuple[int, ...]) -> bytes:
    """Parse a four-byte EnOcean/ELTAKO address.

    Accepted examples:
    - ``00-00-B0-21``
    - ``FF:A6:07:03``
    - ``bytes([0, 0, 0xB0, 0x21])``
    """
    if isinstance(value, (bytes, bytearray)):
        data = bytes(value)
        if len(data) != 4:
            raise InvalidAddressError(f"Address must contain exactly 4 bytes, got {len(data)}")
        return data

    if isinstance(value, (list, tuple)):
        if len(value) != 4:
            raise InvalidAddressError(f"Address must contain exactly 4 parts, got {len(value)}")
        try:
            return bytes(int(part) & 0xFF for part in value)
        except Exception as err:
            raise InvalidAddressError(f"Invalid address parts: {value!r}") from err

    text = str(value or "").strip()
    if not _ADDR_RE.match(text):
        raise InvalidAddressError(f"Invalid ELTAKO address: {value!r}")
    separator = ":" if ":" in text else "-"
    return bytes(int(part, 16) for part in text.split(separator))


def format_address(value: bytes | bytearray | list[int] | tuple[int, ...]) -> str:
    return "-".join(f"{part:02X}" for part in parse_address(value))
