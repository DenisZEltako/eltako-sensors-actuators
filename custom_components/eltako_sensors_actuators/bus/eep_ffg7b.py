from __future__ import annotations

from typing import Any

FFG7B_A5_STATE_MAP: dict[int, str] = {
    0x08: "geschlossen",
    0x0A: "gekippt",
    0x0E: "offen",
}

# FFG7B three-state values plus the known two-state FTKE/FFTE variants that
# share EEP F6-10-00. Keeping them in one decoder is required because EEDTOY
# intentionally offers the products in one common F6-10-00 catalog row.
F6_10_00_STATE_MAP: dict[int, str] = {
    0xF0: "geschlossen",
    0xE0: "offen",
    0xD0: "gekippt",
    0x70: "geschlossen",
    0x50: "offen",
    0x30: "geschlossen",
    0x10: "offen",
}

FFG7B_A5_TEACH_IN = bytes((0x50, 0x48, 0x0D, 0x80))
FFG7B_A5_TEACH_IN_REVERSED = bytes(reversed(FFG7B_A5_TEACH_IN))


def decode_ffg7b_rps(data_byte: int) -> dict[str, Any]:
    """Decode F6-10-00 for FFG7B, FTKE and FFTE.

    Documented FFG7B positions:
      0xF0 closed, 0xE0 open, 0xD0 tilted.

    FTKE/FFTE two-state variants can use the established 0x70/0x50 or
    0x30/0x10 pairs. Those values map to closed/open and never to tilted.
    """
    raw = int(data_byte) & 0xFF
    state = F6_10_00_STATE_MAP.get(raw)
    result: dict[str, Any] = {
        "value": raw,
        "window_state_raw": raw,
        "telegram_type": "f6_10_00_window_state",
        "detected_eep": "F6-10-00",
    }
    if state is not None:
        result.update(
            {
                "window_state": state,
                "open": state != "geschlossen",
                "closed": state == "geschlossen",
                "tilted": state == "gekippt",
                "window_state_family": (
                    "ffg7b_three_state" if raw in {0xF0, 0xE0, 0xD0} else "ftke_ffte_two_state"
                ),
            }
        )
    else:
        result["window_state_unrecognized"] = True
    return result


def _normalize_a5_state_byte(value: int) -> tuple[int | None, str | None]:
    """Return the documented A5 state code and recognition method.

    Normal data uses 0x08/0x0A/0x0E. Some transports retain unrelated upper
    bits or expose the nibble in the upper half-byte. These compatibility
    paths are deliberately restricted to the configured FFG7B profile.
    """
    raw = int(value) & 0xFF
    if raw in FFG7B_A5_STATE_MAP:
        return raw, "exact"

    low_nibble = raw & 0x0F
    if low_nibble in FFG7B_A5_STATE_MAP:
        return low_nibble, "low_nibble"

    high_nibble = (raw >> 4) & 0x0F
    if high_nibble in FFG7B_A5_STATE_MAP:
        return high_nibble, "high_nibble"

    return None, None


def decode_ffg7b_a5(data: bytes | bytearray) -> dict[str, Any]:
    """Decode FFG7B A5-14-09 in both observed byte presentations.

    Standard EnOcean 4BS order is DB3, DB2, DB1, DB0. ELTAKO documentation
    names the state as Data_byte0 and the battery value as Data_byte3. Some
    gateway views display the four payload bytes in the reverse order. Both
    endpoint layouts are supported, followed by a narrowly scoped unique-byte
    fallback.
    """
    payload = bytes(data)
    if len(payload) < 4:
        raise ValueError(f"A5-14-09 expects 4 data bytes, got {len(payload)}")
    payload = payload[:4]

    learn = payload in {FFG7B_A5_TEACH_IN, FFG7B_A5_TEACH_IN_REVERSED}
    result: dict[str, Any] = {
        "value": payload.hex("-"),
        "raw": list(payload),
        "learn": learn,
        "learn_telegram": learn,
        "data_telegram": not learn,
        "telegram_type": "ffg7b_teach_in" if learn else "ffg7b_window_state_a5_14_09",
        "detected_eep": "A5-14-09",
        "data_byte0_raw": payload[3],
        "data_byte1_raw": payload[2],
        "data_byte2_raw": payload[1],
        "data_byte3_raw": payload[0],
    }
    if learn:
        return result

    # Prefer the two documented endpoint layouts. This avoids accidentally
    # treating a battery byte as the state when its low nibble happens to be
    # 8, A or E.
    candidates = [
        (3, 0, "standard_db3_db2_db1_db0"),
        (0, 3, "reversed_data_byte0_first"),
    ]

    selected: tuple[int, int, str, int, str] | None = None
    for state_index, battery_index, layout in candidates:
        normalized, encoding = _normalize_a5_state_byte(payload[state_index])
        if normalized is not None and encoding is not None:
            selected = (state_index, battery_index, layout, normalized, encoding)
            break

    if selected is None:
        matches: list[tuple[int, int, str]] = []
        for index, raw in enumerate(payload):
            normalized, encoding = _normalize_a5_state_byte(raw)
            if normalized is not None and encoding is not None:
                matches.append((index, normalized, encoding))
        if len(matches) == 1:
            state_index, normalized, encoding = matches[0]
            battery_index = 0 if state_index != 0 else 3
            selected = (
                state_index,
                battery_index,
                "unique_state_byte_fallback",
                normalized,
                encoding,
            )

    if selected is None:
        result.update(
            {
                "window_state_unrecognized": True,
                "window_state_candidates": [f"0x{value:02X}" for value in payload],
                "battery_voltage_raw": payload[0],
                "battery_voltage": round(max(0, min(250, payload[0])) / 50.0, 2),
            }
        )
        return result

    state_index, battery_index, layout, normalized_state, encoding = selected
    state = FFG7B_A5_STATE_MAP[normalized_state]
    battery_raw = payload[battery_index]
    result.update(
        {
            "window_state": state,
            "open": state != "geschlossen",
            "closed": state == "geschlossen",
            "tilted": state == "gekippt",
            "window_state_raw": payload[state_index],
            "window_state_normalized": normalized_state,
            "window_state_byte_index": state_index,
            "window_state_encoding": encoding,
            "data_layout": layout,
            "battery_voltage_raw": battery_raw,
            "battery_voltage": round(max(0, min(250, battery_raw)) / 50.0, 2),
        }
    )
    return result


def _parse_hex_bytes(value: Any) -> bytes | None:
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    if isinstance(value, (list, tuple)):
        try:
            return bytes(int(item) & 0xFF for item in value)
        except (TypeError, ValueError):
            return None

    text = str(value or "").strip().replace(" ", "-").replace(":", "-")
    if not text:
        return None
    parts = [part for part in text.split("-") if part]
    try:
        return bytes(int(part, 16) for part in parts)
    except (TypeError, ValueError):
        return None


def _payload_and_org_from_decoded(decoded: dict[str, Any]) -> tuple[bytes | None, str]:
    org_text = str(decoded.get("org") or "").strip().lower()

    payload = _parse_hex_bytes(decoded.get("data_hex"))
    if payload:
        return payload, org_text

    # Compatibility with parser/debug paths that expose only the decoded value.
    value_payload = _parse_hex_bytes(decoded.get("value"))
    if value_payload and len(value_payload) in {1, 4}:
        return value_payload, org_text

    # decode_esp2_message stores the complete serialized ESP2 frame in `raw`.
    # A frame is A5 5A + 11-byte body + checksum. ORG is byte 3 and the four
    # data bytes begin at byte 4 in the serialized representation.
    raw_frame = _parse_hex_bytes(decoded.get("raw"))
    if raw_frame and len(raw_frame) >= 8 and raw_frame[:2] == b"\xA5\x5A":
        if not org_text:
            org_text = f"0x{raw_frame[3]:02x}"
        return raw_frame[4:8], org_text

    return None, org_text


def enrich_ffg7b_decoded(decoded: dict[str, Any]) -> dict[str, Any]:
    """Repair or enrich an FFG7B/FTKE/FFTE decoded telegram in-place.

    This entity-side safety net handles an older YAML selecting A5-14-09 while
    the physical device transmits F6-10-00 (or the reverse). It also recovers
    from decoder paths that supplied only `data_hex`, `value` or the raw ESP2
    frame. State keys from the verified profile decoder deliberately replace
    generic values.
    """
    if not isinstance(decoded, dict):
        return decoded
    if decoded.get("window_state") in {"geschlossen", "gekippt", "offen"}:
        return decoded

    payload, org_text = _payload_and_org_from_decoded(decoded)
    if not payload:
        return decoded

    try:
        if org_text in {"0x05", "5", "05"}:
            repaired = decode_ffg7b_rps(payload[0])
        elif org_text in {"0x07", "7", "07"}:
            repaired = decode_ffg7b_a5(payload[:4])
        elif len(payload) == 1:
            repaired = decode_ffg7b_rps(payload[0])
        elif len(payload) >= 4:
            repaired = decode_ffg7b_a5(payload[:4])
            if "window_state" not in repaired and payload[0] in F6_10_00_STATE_MAP:
                repaired = decode_ffg7b_rps(payload[0])
        else:
            return decoded
    except (TypeError, ValueError, IndexError):
        return decoded

    verified_keys = {
        "window_state",
        "open",
        "closed",
        "tilted",
        "battery_voltage",
        "battery_voltage_raw",
        "window_state_raw",
        "window_state_normalized",
        "window_state_byte_index",
        "window_state_encoding",
        "window_state_family",
        "window_state_unrecognized",
        "window_state_candidates",
        "data_layout",
        "detected_eep",
        "telegram_type",
        "learn",
        "learn_telegram",
        "data_telegram",
    }
    for key, value in repaired.items():
        if key in verified_keys:
            decoded[key] = value
        else:
            decoded.setdefault(key, value)
    return decoded
