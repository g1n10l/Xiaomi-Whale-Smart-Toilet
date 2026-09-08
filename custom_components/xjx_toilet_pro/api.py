"""Local miIO client for Xiaomi Mijia Whale Smart Toilet Cover."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from miio import Device

from .const import MODEL_XJX_TOILET_PRO

AVAILABLE_PROPERTIES: list[str] = [
    "seating",
    "status_airfilter",
    "status_led",
    "status_selfclean",
    "left_day",
]

DEFAULT_TEMPERATURE_LEVEL = 2
DEFAULT_REAR_WASH_STRENGTH = 2
DEFAULT_REAR_WASH_POSITION = 2
DEFAULT_REAR_WASH_MOVING = 1
DEFAULT_REAR_WASH_MASSAGE = 0


@dataclass(slots=True)
class ToiletLidStatus:
    """Parsed toilet-cover state."""

    seating: bool
    air_filter: bool
    led: bool
    self_clean: bool
    water_filter_days_remaining: int | None


class XjxToiletProClient(Device):
    """Synchronous python-miio client for xjx.toilet.pro."""

    _supported_models = [MODEL_XJX_TOILET_PRO]

    def __init__(self, ip: str, token: str, model: str = MODEL_XJX_TOILET_PRO) -> None:
        supported_model = (
            model if model == MODEL_XJX_TOILET_PRO else MODEL_XJX_TOILET_PRO
        )
        super().__init__(ip, token, model=supported_model)
        self._fan_temperature_level = DEFAULT_TEMPERATURE_LEVEL
        self._rear_wash_water_temperature_level = DEFAULT_TEMPERATURE_LEVEL

    def status(self) -> ToiletLidStatus:
        """Retrieve and parse device properties."""
        values = self.get_properties(AVAILABLE_PROPERTIES, max_properties=1)
        data = dict(zip(AVAILABLE_PROPERTIES, values, strict=False))
        return ToiletLidStatus(
            seating=_as_bool(data.get("seating")),
            air_filter=_as_bool(data.get("status_airfilter")),
            led=_as_bool(data.get("status_led")),
            self_clean=_as_bool(data.get("status_selfclean")),
            water_filter_days_remaining=_decode_remaining_days(
                data.get("left_day")
            ),
        )

    def set_self_clean(self, state: bool) -> Any:
        """Turn self-cleaning on or off."""
        if state:
            return self.send("self_clean_on")
        return self.send("func_off", ["self_clean"])

    def set_led(self, state: bool) -> Any:
        """Turn the night LED on or off."""
        if state:
            return self.send("night_led_on")
        return self.send("func_off", ["night_led"])

    def set_warm_air_drying(self, state: bool) -> Any:
        """Start or stop warm-air drying."""
        if state:
            return self.send("warm_dry_on", [self._fan_temperature_level])
        return self.send("func_off", ["warm_dry"])

    def set_fan_temperature(self, level: int) -> Any:
        """Set the warm-air temperature level."""
        _validate_temperature_level(level)
        result = self.send("set_fan_temp", [level])
        self._fan_temperature_level = level
        return result

    def set_rear_wash(self, state: bool) -> Any:
        """Start or stop rear washing."""
        if state:
            return self.send(
                "tun_wash_on",
                [
                    self._rear_wash_water_temperature_level,
                    DEFAULT_REAR_WASH_STRENGTH,
                    DEFAULT_REAR_WASH_POSITION,
                    DEFAULT_REAR_WASH_MOVING,
                    DEFAULT_REAR_WASH_MASSAGE,
                ],
            )
        return self.send("func_off", ["tun_wash"])

    def set_rear_wash_water_temperature(self, level: int) -> Any:
        """Set the rear-wash water temperature level."""
        _validate_temperature_level(level)
        result = self.send("set_water_temp_t", [level])
        self._rear_wash_water_temperature_level = level
        return result

    def remember_fan_temperature(self, level: int) -> None:
        """Remember a temperature level without sending a command."""
        _validate_temperature_level(level)
        self._fan_temperature_level = level

    def remember_rear_wash_water_temperature(self, level: int) -> None:
        """Remember a rear-wash water temperature without sending a command."""
        _validate_temperature_level(level)
        self._rear_wash_water_temperature_level = level

    def raw_command(
        self,
        command: str,
        params: list[Any] | dict[str, Any] | None = None,
    ) -> Any:
        """Send a raw miIO command."""
        return self.send(command, params)


def _as_bool(value: Any) -> bool:
    """Convert common miIO scalar values to bool without raising on None."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    try:
        return bool(int(value))
    except (TypeError, ValueError):
        return bool(value)


def _validate_temperature_level(level: int) -> None:
    """Validate a three-level temperature setting."""
    if level not in (1, 2, 3):
        raise ValueError("Temperature level must be 1, 2 or 3")


def _decode_remaining_days(value: Any) -> int | None:
    """Decode the device's 1000-offset remaining-days value."""
    try:
        encoded_days = int(value)
    except (TypeError, ValueError):
        return None
    return encoded_days - 1000 if encoded_days >= 1000 else None
