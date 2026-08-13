from __future__ import annotations

from dataclasses import dataclass

NEW_FRAME_MIN_LEN = 10
CONNECT_TRAP_MARKER = 0x01
ELECTRONIC_TRAP_MARKER = 0x02
MANUFACTURER_ID = 3003
STATUS_READY = 0x00
STATUS_TRIGGERED = 0x01
MODEL_CONNECT_SUPERCAT = "Connect SuperCat"
MODEL_ELECTRONIC_SUPERCAT = "Electronic SuperCat"
MODEL_LEGACY_SUPERCAT = "SuperCat (legacy protocol)"
ELECTRONIC_BATTERY_MAX_VOLTS = 6.0


@dataclass
class DecodedTrapFrame:
    version: int
    device_type: int
    event_counter: int | None
    status: int
    is_tripped: bool | None
    trap_id: str
    legacy_trap_ids: tuple[str, ...]
    battery_raw: int | None
    battery_volts: float | None
    model: str


def _battery_to_volts(raw: int | None) -> float | None:
    """Convert a raw battery byte to volts."""
    if raw is None:
        return None
    return round((raw * 3.6) / 255.0, 2)


def _electronic_battery_to_volts(raw: int) -> float:
    """Estimate the Electronic SuperCat pack voltage from its battery byte."""
    return round((raw * ELECTRONIC_BATTERY_MAX_VOLTS) / 255.0, 2)


def _decode_binary_status(status: int) -> bool | None:
    """Decode the ready/triggered flag shared by SWISSINNO advertisements."""
    if status == STATUS_READY:
        return False
    if status == STATUS_TRIGGERED:
        return True
    return None


def _hex_id(value: bytes) -> str:
    """Return the uppercase hexadecimal form used by legacy entity IDs."""
    return value.hex().upper()


def decode_frame(payload: bytes) -> DecodedTrapFrame | None:
    """Decode SWISSINNO BLE manufacturer payload.

    Supports:
    - Electronic 10-byte format with a trailing ready/triggered flag
    - Connect 10-byte format with a leading ready/triggered flag
    - Legacy format with a leading ready/triggered flag
    """
    if len(payload) < 6:
        return None

    # Electronic SuperCat traps use byte 6 as a layout marker, byte 7 as the
    # battery-related value, and byte 9 as the binary alarm state. Byte 8 has
    # been observed changing after configuration writes while byte 7 remained
    # stable, so it must not be interpreted as the battery value's high byte.
    # Byte 0 varies between observed advertisements and is not the state for
    # this family.
    if len(payload) >= NEW_FRAME_MIN_LEN and payload[6] == ELECTRONIC_TRAP_MARKER:
        trap_id_bytes = payload[2:6]
        if not any(trap_id_bytes):
            return None

        status = payload[9]
        battery_raw = payload[7]

        return DecodedTrapFrame(
            version=payload[0],
            device_type=payload[1],
            event_counter=None,
            status=status,
            is_tripped=_decode_binary_status(status),
            trap_id=_hex_id(trap_id_bytes),
            legacy_trap_ids=(_hex_id(trap_id_bytes),),
            battery_raw=battery_raw,
            battery_volts=_electronic_battery_to_volts(battery_raw),
            model=MODEL_ELECTRONIC_SUPERCAT,
        )

    # Connect SuperCat format (10 bytes minimum).
    # Example ready frame: 00 3F CE 03 04 00 01 DA 03 00
    # Byte 0 is the binary status, bytes 2-5 are the stable hardware ID, and
    # byte 6 identifies the Connect family. Earlier versions incorrectly
    # treated bytes 2-3 as a counter and byte 4 (part of the ID) as status.
    if (
        len(payload) >= NEW_FRAME_MIN_LEN
        and payload[6] == CONNECT_TRAP_MARKER
    ):
        status = payload[0]
        trap_id_bytes = payload[2:6]
        if not any(trap_id_bytes):
            return None

        battery_raw = payload[7] if len(payload) > 7 else None
        battery_volts = _battery_to_volts(battery_raw)

        trap_id = _hex_id(trap_id_bytes)
        return DecodedTrapFrame(
            version=payload[1],
            device_type=payload[6],
            event_counter=None,
            status=status,
            is_tripped=_decode_binary_status(status),
            trap_id=trap_id,
            # Version 1.0.14 used payload[1:4] for Connect identities.
            legacy_trap_ids=(trap_id, _hex_id(payload[1:4])),
            battery_raw=battery_raw,
            battery_volts=battery_volts,
            model=MODEL_CONNECT_SUPERCAT,
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

    status = payload[0]

    battery_raw = payload[7] if len(payload) > 7 else None
    battery_volts = _battery_to_volts(battery_raw)

    return DecodedTrapFrame(
        version=version,
        device_type=-1,
        event_counter=None,
        status=status,
        is_tripped=_decode_binary_status(status),
        trap_id=trap_id,
        legacy_trap_ids=(trap_id,),
        battery_raw=battery_raw,
        battery_volts=battery_volts,
        model=MODEL_LEGACY_SUPERCAT,
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
