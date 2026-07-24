from __future__ import annotations

"""EEP A5-20-04 helpers for FUTH55ED -> FKS-H Hora responses."""

from collections.abc import Iterable
from typing import Any

DATA_TELEGRAM_BIT = 0x08


def decode_a5_20_04_controller_telegram(data: bytes | bytearray | Iterable[int]) -> dict[str, Any]:
    """Decode the direction-2 response sent from FUTH55ED to the valve.

    The stable engineering values defined by A5-20-04 direction 2 are exposed:
    actuator command 0..100 % and temperature set point 10..30 C. Remaining
    control bits stay available as raw diagnostics so no undocumented ELTAKO
    bit assignment is invented.
    """
    raw = bytes(data)
    if len(raw) != 4:
        raise ValueError(f"A5-20-04 expects 4 data bytes, got {len(raw)}")
    db3, db2, db1, db0 = raw
    learn = not bool(db0 & DATA_TELEGRAM_BIT)
    result: dict[str, Any] = {
        "value": raw.hex("-"),
        "learn": learn,
        "learn_telegram": learn,
        "data_telegram": not learn,
        "direction": "to_actuator",
        "futh55ed_response": not learn,
        "telegram_type": "futh55ed_fks_hora_teach_in" if learn else "futh55ed_fks_hora_response",
    }
    if learn:
        result["teach_in_query_data"] = raw
        return result

    result.update(
        {
            "valve_position_command": max(0, min(100, int(db3))),
            "target_temperature_command": round(10.0 + (db2 / 255.0) * 20.0, 1),
            "control_raw": int(db1),
            "status_raw": int(db0),
        }
    )
    return result
