"""Local miIO client for Xiaomi Mijia Whale Smart Toilet Cover."""

from __future__ import annotations

from dataclasses import dataclass
import threading
import time
from typing import Any, ClassVar

from miio import Device

from .const import MODEL_XJX_TOILET_PRO

# On firmware 2.1.3, the issue reporter confirmed these two properties.
# Polling status_airfilter and status_led timed out; status_selfclean returned
# "ok" instead of a state and could make the entire update unavailable.
AVAILABLE_PROPERTIES: list[str] = [
    "seating",
    "left_day",
]

# Firmware 2.1.3 expects levels, not degrees. The issue reporter measured
# level 2 for the seat, dryer and wash; levels 1 and 3 are inferred.
LEVELS: tuple[int, ...] = (1, 2, 3)
SEAT_LEVELS: tuple[int, ...] = (0, 1, 2, 3)

# Minimum gap between two miIO packets; the issue reports failures with
# back-to-back commands on firmware 2.1.3.
MIN_COMMAND_GAP_SECONDS = 0.5

DEFAULT_FAN_TEMPERATURE = 2
DEFAULT_SEAT_TEMPERATURE = 0
DEFAULT_REAR_WASH_WATER_TEMPERATURE = 2
DEFAULT_REAR_WASH_STRENGTH = 2
DEFAULT_REAR_WASH_POSITION = 2
DEFAULT_REAR_WASH_MOVING = 1
DEFAULT_REAR_WASH_MASSAGE = 0


@dataclass(slots=True)
class ToiletLidStatus:
    """Parsed toilet-cover state."""

    seating: bool
    water_filter_days_remaining: int | None


class XjxToiletProClient(Device):
    """Synchronous python-miio client for xjx.toilet.pro."""

    _supported_models: ClassVar[list[str]] = [MODEL_XJX_TOILET_PRO]

    def __init__(self, ip: str, token: str, model: str = MODEL_XJX_TOILET_PRO) -> None:
        supported_model = (
            model if model == MODEL_XJX_TOILET_PRO else MODEL_XJX_TOILET_PRO
        )
        super().__init__(ip, token, model=supported_model)
        self._fan_temperature = DEFAULT_FAN_TEMPERATURE
        self._seat_temperature = DEFAULT_SEAT_TEMPERATURE
        self._rear_wash_water_temperature = DEFAULT_REAR_WASH_WATER_TEMPERATURE
        self._io_lock = threading.RLock()
        self._last_io = 0.0

    def send(self, command: str, parameters: Any = None, *args: Any, **kwargs: Any) -> Any:
        """Send one miIO packet at a time with a small gap between packets."""
        with self._io_lock:
            wait = MIN_COMMAND_GAP_SECONDS - (time.monotonic() - self._last_io)
            if wait > 0:
                time.sleep(wait)
            try:
                return super().send(command, parameters, *args, **kwargs)
            finally:
                self._last_io = time.monotonic()

    def status(self) -> ToiletLidStatus:
        """Retrieve and parse device properties."""
        values = self.get_properties(AVAILABLE_PROPERTIES, max_properties=1)
        data = dict(zip(AVAILABLE_PROPERTIES, values, strict=False))
        return ToiletLidStatus(
            seating=_as_bool(data.get("seating")),
            water_filter_days_remaining=_decode_remaining_days(data.get("left_day")),
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
            return self.send("warm_dry_on", [self._fan_temperature])
        return self.send("func_off", ["warm_dry"])

    def set_fan_temperature(self, temperature: int) -> Any:
        """Apply a new temperature during active warm-air drying."""
        _validate_temperature(temperature, LEVELS)
        result = self.send("warm_dry_on", [temperature])
        self._fan_temperature = temperature
        return result

    def set_seat_temperature(self, temperature: int) -> Any:
        """Set the seat-ring temperature."""
        _validate_temperature(temperature, SEAT_LEVELS)
        result = self.send("set_seat_temp", [temperature])
        self._seat_temperature = temperature
        return result

    def set_rear_wash(self, state: bool) -> Any:
        """Start or stop rear washing."""
        if state:
            return self.send(
                "tun_wash_on",
                [
                    self._rear_wash_water_temperature,
                    DEFAULT_REAR_WASH_STRENGTH,
                    DEFAULT_REAR_WASH_POSITION,
                    DEFAULT_REAR_WASH_MOVING,
                    DEFAULT_REAR_WASH_MASSAGE,
                ],
            )
        return self.send("func_off", ["tun_wash"])

    def set_rear_wash_water_temperature(self, temperature: int) -> Any:
        """Apply a new water temperature during active rear washing."""
        _validate_temperature(temperature, LEVELS)
        result = self.send(
            "tun_wash_on",
            [
                temperature,
                DEFAULT_REAR_WASH_STRENGTH,
                DEFAULT_REAR_WASH_POSITION,
                DEFAULT_REAR_WASH_MOVING,
                DEFAULT_REAR_WASH_MASSAGE,
            ],
        )
        self._rear_wash_water_temperature = temperature
        return result

    def remember_fan_temperature(self, temperature: int) -> None:
        """Remember an air temperature without sending a command."""
        _validate_temperature(temperature, LEVELS)
        self._fan_temperature = temperature

    def remember_seat_temperature(self, temperature: int) -> None:
        """Remember a seat temperature without sending a command."""
        _validate_temperature(temperature, SEAT_LEVELS)
        self._seat_temperature = temperature

    def remember_rear_wash_water_temperature(self, temperature: int) -> None:
        """Remember a water temperature without sending a command."""
        _validate_temperature(temperature, LEVELS)
        self._rear_wash_water_temperature = temperature

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


def _validate_temperature(temperature: int, allowed: tuple[int, ...]) -> None:
    """Validate a device temperature level."""
    if temperature not in allowed:
        raise ValueError(f"Temperature level must be one of: {allowed}")


def _decode_remaining_days(value: Any) -> int | None:
    """Decode the device's 1000-offset remaining-days value."""
    try:
        encoded_days = int(value)
    except (TypeError, ValueError):
        return None
    return encoded_days - 1000 if encoded_days >= 1000 else None
