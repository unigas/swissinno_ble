from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

NEW_FRAME_MIN_LEN = 10
MANUFACTURER_ID = 3003


@dataclass
class DecodedTrapFrame:
    version: int
    device_type: int
    event_counter: Optional[int]
    status: int
    is_tripped: bool
    trap_id: str
    battery_raw: Optional[int]
    battery_volts: Optional[float]


def _battery_to_volts(raw: Optional[int]) -> Optional[float]:
    """Convert a raw battery byte to volts."""
    if raw is None:
        return None
    return round((raw * 3.6) / 255.0, 2)


def decode_frame(payload: bytes) -> Optional[DecodedTrapFrame]:
    """Decode SWISSINNO BLE manufacturer payload.

    Supports both:
    - New 10-byte format (2024/2025 traps)
    - Old format (legacy traps)
    """
    if not payload:
        return None

    # ----------------------------------------------------------------------
    # NEW FORMAT (10 bytes minimum)
    # Example: 00 3F CE 03 04 00 01 DA 03 00
    # ----------------------------------------------------------------------
    if len(payload) >= NEW_FRAME_MIN_LEN and payload[0] == 0x00:
        version = payload[0]
        device_type = payload[1]

        event_counter = payload[2] | (payload[3] << 8)
        status = payload[4]

        # New traps treat statuses 1–3 as "tripped"
        is_tripped = status in (0x01, 0x02, 0x03)

        # Stable trap ID based on device type + counter bytes
        trap_id = f"{device_type:02X}{payload[2]:02X}{payload[3]:02X}"

        battery_raw = payload[7] if len(payload) > 7 else None
        battery_volts = _battery_to_volts(battery_raw)

        return DecodedTrapFrame(
            version=version,
            device_type=device_type,
            event_counter=event_counter,
            status=status,
            is_tripped=is_tripped,
            trap_id=trap_id,
            battery_raw=battery_raw,
            battery_volts=battery_volts,
        )

    # ----------------------------------------------------------------------
    # OLD FORMAT (legacy SuperCat)
    # Format example you currently use:
    # [0] == 0x01 means tripped
    # bytes[2:6] form the trap_id
    # byte 7 = battery
    # ----------------------------------------------------------------------
    version = -1

    trap_id = "".join(f"{b:02X}" for b in payload[2:6]) if len(payload) >= 6 else "UNKNOWN"

    is_tripped = payload[0] == 0x01

    battery_raw = payload[7] if len(payload) > 7 else None
    battery_volts = _battery_to_volts(battery_raw)

    return DecodedTrapFrame(
        version=version,
        device_type=-1,
        event_counter=None,
        status=payload[0],
        is_tripped=is_tripped,
        trap_id=trap_id,
        battery_raw=battery_raw,
        battery_volts=battery_volts,
    )
