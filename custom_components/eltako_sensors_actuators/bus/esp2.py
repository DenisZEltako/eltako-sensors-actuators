from __future__ import annotations

from dataclasses import dataclass

PREAMBLE = b"\xA5\x5A"
ORG_RPS = 0x05
ORG_1BS = 0x06
ORG_4BS = 0x07
_OUTGOING_CODE = (3 << 5) + 11  # 0x6B, ESP2 transmit telegram
_INCOMING_CODE = (0 << 5) + 11  # 0x0B, ESP2 receive telegram


@dataclass(frozen=True, slots=True)
class ESP2Message:
    """Minimal ESP2 message representation used by this integration."""

    body: bytes

    @property
    def org(self) -> int:
        return self.body[1]

    def serialize(self) -> bytes:
        if len(self.body) != 11:
            raise ValueError(f"ESP2 body must be 11 bytes, got {len(self.body)}")
        return PREAMBLE + self.body + bytes([sum(self.body) & 0xFF])

    @classmethod
    def parse(cls, frame: bytes) -> "ESP2Message":
        if len(frame) != 14:
            raise ValueError(f"ESP2 frame must be 14 bytes, got {len(frame)}")
        if not frame.startswith(PREAMBLE):
            raise ValueError("ESP2 preamble A5 5A missing")
        body = frame[2:13]
        checksum = frame[13]
        if (sum(body) & 0xFF) != checksum:
            raise ValueError("ESP2 checksum mismatch")
        return cls(body)


def build_regular_4bs(address: bytes, data: bytes | bytearray, status: int = 0x00, outgoing: bool = True) -> ESP2Message:
    if len(address) != 4:
        raise ValueError("4BS address must be 4 bytes")
    if len(data) != 4:
        raise ValueError("4BS data must be 4 bytes")
    code = _OUTGOING_CODE if outgoing else _INCOMING_CODE
    body = bytes([code, ORG_4BS, *bytes(data), *address, status & 0xFF])
    return ESP2Message(body)


def build_rps(address: bytes, data_byte: int, status: int = 0x30, outgoing: bool = True) -> ESP2Message:
    if len(address) != 4:
        raise ValueError("RPS address must be 4 bytes")
    code = _OUTGOING_CODE if outgoing else _INCOMING_CODE
    body = bytes([code, ORG_RPS, data_byte & 0xFF, 0, 0, 0, *address, status & 0xFF])
    return ESP2Message(body)
