"""Models for AirGradient."""

from __future__ import annotations

from dataclasses import dataclass, field

from mashumaro import field_options
from mashumaro.mixins.orjson import DataClassORJSONMixin


@dataclass
class Status(DataClassORJSONMixin):
    """Status model."""

    signal_strength: int = field(metadata=field_options(alias="wifi"))
    serial_number: str = field(metadata=field_options(alias="serialno"))
    rco2: int
    pm01: int
    pm02: int
    pm10: int
    pm003_count: int
    tvoc_index: int
    tvoc_raw: int
    nox_index: int
    nox_raw: int
    ambient_temperature: float = field(metadata=field_options(alias="atmp"))
    relative_humidity: float = field(metadata=field_options(alias="rhum"))
    boot_time: int = field(metadata=field_options(alias="boot"))
