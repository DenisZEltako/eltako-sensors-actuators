from __future__ import annotations

from .esp2 import ESP2Message, ORG_4BS, ORG_RPS, ORG_1BS

SYNC = 0x55
PACKET_TYPE_RADIO_ERP1 = 0x01
RORG_4BS = 0xA5
RORG_RPS = 0xF6
RORG_1BS = 0xD5


def crc8_esp3(data: bytes | bytearray) -> int:
    """CRC8 used by EnOcean ESP3, polynomial x8+x2+x+1 (0x07)."""
    crc = 0
    for byte in bytes(data):
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc & 0xFF


def build_esp3_packet(data: bytes, optional: bytes = b"", packet_type: int = PACKET_TYPE_RADIO_ERP1) -> bytes:
    if len(data) > 0xFFFF:
        raise ValueError("ESP3 data too long")
    if len(optional) > 0xFF:
        raise ValueError("ESP3 optional data too long")
    header = bytes([(len(data) >> 8) & 0xFF, len(data) & 0xFF, len(optional) & 0xFF, packet_type & 0xFF])
    return bytes([SYNC]) + header + bytes([crc8_esp3(header)]) + data + optional + bytes([crc8_esp3(data + optional)])


def esp2_to_esp3_radio_erp1(message: ESP2Message | bytes | bytearray) -> bytes:
    """Convert the integration's internal ESP2 ERP frame to an ESP3 RADIO_ERP1 packet.

    The internal builders already create ERP payloads as ESP2 bodies:
    body[1] = ORG, body[2:6] = data bytes, body[6:10] = sender id,
    body[10] = status.  ESP3 RADIO_ERP1 uses RORG + DATA + SENDER + STATUS
    plus optional TX fields.
    """
    if isinstance(message, ESP2Message):
        body = message.body
    else:
        raw = bytes(message)
        if len(raw) == 14 and raw[:2] == b"\xA5\x5A":
            body = raw[2:13]
        elif len(raw) == 11:
            body = raw
        else:
            raise ValueError(f"Cannot convert raw frame with length {len(raw)} to ESP3")

    org = body[1]
    sender = body[6:10]
    status = body[10]

    if org == ORG_4BS:
        data = bytes([RORG_4BS]) + body[2:6] + sender + bytes([status])
    elif org == ORG_RPS:
        data = bytes([RORG_RPS, body[2]]) + sender + bytes([status])
    elif org == ORG_1BS:
        data = bytes([RORG_1BS, body[2]]) + sender + bytes([status])
    else:
        raise ValueError(f"Unsupported ESP2 ORG 0x{org:02X} for ESP3 RADIO_ERP1")

    # TX optional data: subtelegram count, destination broadcast, dBm placeholder, security level.
    optional = bytes([0x03, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00])
    return build_esp3_packet(data, optional, PACKET_TYPE_RADIO_ERP1)


def build_esp3_radio_erp1_4bs_direct(sender: bytes, data4: bytes, *, status: int = 0x80, destination: bytes | None = None, subtelegram_count: int = 3) -> bytes:
    """Build an ESP3 RADIO_ERP1 4BS TX packet with optional destination id.

    ESP2 4BS frames cannot carry a destination id. The verified GFA5 reference
    shows FRGBW71L color telegrams as addressed to the actuator id. This helper
    creates the corresponding ESP3 TX packet so the optional TX destination can
    be set to the FRGBW actuator id instead of broadcast FFFFFFFF.
    """
    if len(sender) != 4:
        raise ValueError("sender must be 4 bytes")
    if len(data4) != 4:
        raise ValueError("4BS data must be 4 bytes")
    if destination is None:
        destination = b"\xFF\xFF\xFF\xFF"
    if len(destination) != 4:
        raise ValueError("destination must be 4 bytes")
    data = bytes([RORG_4BS]) + bytes(data4) + bytes(sender) + bytes([status & 0xFF])
    optional = bytes([max(1, min(15, int(subtelegram_count)))]) + bytes(destination) + bytes([0xFF, 0x00])
    return build_esp3_packet(data, optional, PACKET_TYPE_RADIO_ERP1)
