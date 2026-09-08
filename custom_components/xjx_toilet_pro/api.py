"""Local miIO client for Xiaomi Mijia Whale Smart Toilet Cover."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from miio import Device

from .const import MODEL_XJX_TOILET_PRO

AVAILABLE_PROPERTIES: dict[str, list[str]] = {
    MODEL_XJX_TOILET_PRO: [
        "seating",
        "status_airfilter",
        "status_led",
        "status_selfclean",
    ]
}

DEFAULT_FAN_TEMPERATURE_LEVEL = 2
DEFAULT_REAR_WASH_WATER_TEMPERATURE_LEVEL = 2
DEFAULT_REAR_WASH_WATER_STRENGTH_LEVEL = 2
DEFAULT_REAR_WASH_NOZZLE_POSITION = 2


@dataclass(slots=True)
class ToiletlidStatus:
    """Parsed toilet-cover state."""

    seating: bool
    air_filter: bool
    led: bool
    self_clean: bool
    warm_air_drying: bool | None
    rear_wash: bool | None
    fan_temperature: int | None
    rear_wash_water_temperature: int | None


class XjxToiletProClient(Device):
    """Synchronous python-miio client for xjx.toilet.pro."""

    _supported_models = list(AVAILABLE_PROPERTIES)

    def __init__(self, ip: str, token: str, model: str = MODEL_XJX_TOILET_PRO) -> None:
        super().__init__(ip, token, model=model)
        self._model = model if model in AVAILABLE_PROPERTIES else MODEL_XJX_TOILET_PRO
        self._fan_temperature_level = DEFAULT_FAN_TEMPERATURE_LEVEL
        self._rear_wash_water_temperature_level = (
            DEFAULT_REAR_WASH_WATER_TEMPERATURE_LEVEL
        )

    def status(self) -> ToiletlidStatus:
        """Retrieve and parse device properties."""
        properties = AVAILABLE_PROPERTIES[self._model]
        values = self.get_properties(properties, max_properties=1)
        data = dict(zip(properties, values, strict=False))
        return ToiletlidStatus(
            seating=_as_bool(data.get("seating")),
            air_filter=_as_bool(data.get("status_airfilter")),
            led=_as_bool(data.get("status_led")),
            self_clean=_as_bool(data.get("status_selfclean")),
            warm_air_drying=None,
            rear_wash=None,
            fan_temperature=None,
            rear_wash_water_temperature=None,
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
        self._validate_fan_temperature(level)
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
                    DEFAULT_REAR_WASH_WATER_STRENGTH_LEVEL,
                    DEFAULT_REAR_WASH_NOZZLE_POSITION,
                    1,
                    0,
                ],
            )
        return self.send("func_off", ["tun_wash"])

    def set_rear_wash_water_temperature(self, level: int) -> Any:
        """Set the rear-wash water temperature level."""
        self._validate_temperature_level(level)
        result = self.send("set_water_temp_t", [level])
        self._rear_wash_water_temperature_level = level
        return result

    def remember_fan_temperature(self, level: int) -> None:
        """Remember a temperature level without sending a command."""
        self._validate_fan_temperature(level)
        self._fan_temperature_level = level

    def remember_rear_wash_water_temperature(self, level: int) -> None:
        """Remember a rear-wash water temperature without sending a command."""
        self._validate_temperature_level(level)
        self._rear_wash_water_temperature_level = level

    @staticmethod
    def _validate_fan_temperature(level: int) -> None:
        """Validate a warm-air temperature level."""
        XjxToiletProClient._validate_temperature_level(level)

    @staticmethod
    def _validate_temperature_level(level: int) -> None:
        """Validate a three-level temperature setting."""
        if level not in (1, 2, 3):
            raise ValueError("Temperature level must be 1, 2 or 3")

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
