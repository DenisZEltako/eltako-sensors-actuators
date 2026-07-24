from __future__ import annotations

"""EEP A5-10-12 decoder used by the ELTAKO FUTH55ED Hygrostat mode."""

from collections.abc import Iterable
from typing import Any

LEARN_TELEGRAM = bytes((0x40, 0x90, 0x0D, 0x80))
DATA_TELEGRAM_BIT = 0x08


def decode_a5_10_12(data: bytes | bytearray | Iterable[int]) -> dict[str, Any]:
    raw = bytes(data)
    if len(raw) != 4:
        raise ValueError(f"A5-10-12 expects 4 data bytes, got {len(raw)}")
    db3, db2, db1, db0 = raw
    learn = raw == LEARN_TELEGRAM or not bool(db0 & DATA_TELEGRAM_BIT)
    result: dict[str, Any] = {
        "value": raw.hex("-"),
        "learn": learn,
        "learn_telegram": learn,
        "data_telegram": not learn,
        "telegram_type": "futh55ed_hygrostat_teach_in" if learn else "futh55ed_hygrostat",
    }
    if learn:
        result["teach_in_query_data"] = raw
        return result

    # EEP A5-10-12: DB3 humidity, DB2 set point (0..255),
    # DB1 inverse actual temperature 0..40 C. The set point is deliberately
    # kept as its standardized raw value because ELTAKO does not define an
    # absolute Celsius conversion for this FUTH55ED operating mode here.
    result.update(
        {
            "humidity": round(max(0, min(250, db3)) / 250.0 * 100.0, 1),
            "setpoint_raw": int(db2),
            "temperature": round(((255 - db1) / 255.0) * 40.0, 1),
            "db3_humidity_raw": int(db3),
            "db2_setpoint_raw": int(db2),
            "db1_temperature_raw": int(db1),
            "db0_status_raw": int(db0),
        }
    )
    return result
