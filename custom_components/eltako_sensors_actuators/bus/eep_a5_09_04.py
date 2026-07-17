from __future__ import annotations

from typing import Any

FCO2TF65_TEACH_IN = bytes((0x24, 0x20, 0x0D, 0x80))


def decode_a5_09_04(data: bytes) -> dict[str, Any]:
    """Decode ELTAKO FCO2TF65 telegrams using EEP A5-09-04.

    ELTAKO byte layout:
      DB3: relative humidity 0..100 % encoded as 0..200
      DB2: CO2 0..2550 ppm encoded as 0..255
      DB1: temperature 0..51 C encoded as 0..255
      DB0: status/LRN bits

    The known teach-in telegram 24-20-0D-80 must never overwrite measured
    values. CO2 is deliberately calculated as DB2 * 10 so the mapping is
    explicit and cannot be affected by generic concentration scaling.
    """
    if len(data) != 4:
        raise ValueError(f"A5-09-04 expects exactly 4 data bytes, got {len(data)}")

    db3, db2, db1, db0 = data
    learn = data == FCO2TF65_TEACH_IN or not bool(db0 & 0x08)

    result: dict[str, Any] = {
        "learn": learn,
        "learn_telegram": learn,
        "data_telegram": not learn,
        "data_hex": data.hex("-"),
        "value": data.hex("-"),
        "raw": [db3, db2, db1, db0],
        "db3_humidity_raw": db3,
        "db2_co2_raw": db2,
        "db1_temperature_raw": db1,
        "db0_status_raw": db0,
        "telegram_type": "fco2tf65_teach_in" if learn else "fco2tf65_co2_temperature_humidity",
    }

    if learn:
        return result

    humidity = round(min(db3, 200) / 2.0, 1)
    carbon_dioxide = int(db2) * 10
    temperature = round(int(db1) / 5.0, 1)

    result.update(
        {
            "humidity": humidity,
            "carbon_dioxide": carbon_dioxide,
            "co2": carbon_dioxide,
            "temperature": temperature,
        }
    )
    return result
