from __future__ import annotations

from dataclasses import dataclass

NEW_FRAME_MIN_LEN = 10
ELECTRONIC_TRAP_MARKER = 0x02
MANUFACTURER_ID = 3003


@dataclass
class DecodedTrapFrame:
    version: int
    device_type: int
    event_counter: int | None
    status: int
    is_tripped: bool
    trap_id: str
    battery_raw: int | None
    battery_volts: float | None


def _battery_to_volts(raw: int | None) -> float | None:
    """Convert a raw battery byte to volts."""
    if raw is None:
        return None
    return round((raw * 3.6) / 255.0, 2)


def _extended_battery_to_volts(raw: int) -> float:
    """Convert the two-byte battery value used by newer traps to volts."""
    return round(raw / 156.0, 2)


def decode_frame(payload: bytes) -> DecodedTrapFrame | None:
    """Decode SWISSINNO BLE manufacturer payload.

    Supports:
    - Extended 10-byte format with two-byte battery and trailing alarm state
    - 2024/2025 10-byte format with one-byte battery
    - Legacy format
    """
    if len(payload) < 6:
        return None

    # Newer SuperCat traps use byte 6 as a layout marker, bytes 7-8 as a
    # little-endian battery value, and byte 9 as the alarm state. Byte 0 varies
    # between observed ready/triggered advertisements, so it is not used as the
    # state indicator for this layout.
    if len(payload) >= NEW_FRAME_MIN_LEN and payload[6] == ELECTRONIC_TRAP_MARKER:
        trap_id_bytes = payload[2:6]
        if not any(trap_id_bytes):
            return None

        status = payload[9]
        battery_raw = int.from_bytes(payload[7:9], "little")

        return DecodedTrapFrame(
            version=payload[0],
            device_type=payload[1],
            event_counter=None,
            status=status,
            is_tripped=status == 0x01,
            trap_id="".join(f"{byte:02X}" for byte in trap_id_bytes),
            battery_raw=battery_raw,
            battery_volts=_extended_battery_to_volts(battery_raw),
        )

    # ----------------------------------------------------------------------
    # NEW FORMAT (10 bytes minimum)
    # Example: 00 3F CE 03 04 00 01 DA 03 00
    # ----------------------------------------------------------------------
    if len(payload) >= NEW_FRAME_MIN_LEN and payload[0] == 0x00:
        version = payload[0]
        device_type = payload[1]

        event_counter = payload[2] | (payload[3] << 8)
        status = payload[4]

        # New traps treat statuses 1-3 as "tripped"
        is_tripped = status in (0x01, 0x02, 0x03)

        # Frame-local ID retained for backwards compatibility. Entity identity
        # must use the Bluetooth address because these bytes include a counter.
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

    trap_id = (
        "".join(f"{b:02X}" for b in payload[2:6]) if len(payload) >= 6 else "UNKNOWN"
    )

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


def supports_remote_reset(payload: bytes) -> bool:
    """Return whether this trap family supports the documented app reset.

    Electronic traps use marker 0x02 and intentionally require a physical
    power cycle for safety. Connect SuperCat and legacy devices retain the
    reset button.
    """
    return decode_frame(payload) is not None and not (
        len(payload) >= NEW_FRAME_MIN_LEN
        and payload[6] == ELECTRONIC_TRAP_MARKER
    )
