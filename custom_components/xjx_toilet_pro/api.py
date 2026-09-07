"""Local miIO client for Xiaomi Mijia Whale Smart Toilet Cover."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from miio import Device, DeviceException

from .const import MODEL_XJX_TOILET_PRO

AVAILABLE_PROPERTIES: dict[str, list[str]] = {
    MODEL_XJX_TOILET_PRO: [
        "seating",
        "status_airfilter",
        "status_led",
        "status_selfclean",
    ]
}


@dataclass(slots=True)
class ToiletlidStatus:
    """Parsed toilet-cover state."""

    seating: bool
    air_filter: bool
    led: bool
    self_clean: bool
    fan_temperature: int | None


class XjxToiletProClient(Device):
    """Synchronous python-miio client for xjx.toilet.pro."""

    def __init__(self, ip: str, token: str, model: str = MODEL_XJX_TOILET_PRO) -> None:
        super().__init__(ip, token, model=model)
        self._model = model if model in AVAILABLE_PROPERTIES else MODEL_XJX_TOILET_PRO

    def status(self) -> ToiletlidStatus:
        """Retrieve and parse device properties."""
        properties = AVAILABLE_PROPERTIES[self._model]
        values = self.get_properties(properties, max_properties=1)
        data = dict(zip(properties, values, strict=False))
        # Some firmware revisions only expose fan_temp while warm-air drying is
        # active. Query it separately so a timeout does not make every entity
        # unavailable.
        fan_temperature: int | None = None
        try:
            fan_values = self.get_properties(["fan_temp"], max_properties=1)
            if fan_values:
                fan_temperature = _as_int(fan_values[0])
        except DeviceException:
            pass

        return ToiletlidStatus(
            seating=_as_bool(data.get("seating")),
            air_filter=_as_bool(data.get("status_airfilter")),
            led=_as_bool(data.get("status_led")),
            self_clean=_as_bool(data.get("status_selfclean")),
            fan_temperature=fan_temperature,
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

    def set_fan_temperature(self, level: int) -> Any:
        """Set the warm-air drying temperature level."""
        if level not in (1, 2, 3):
            raise ValueError("Fan temperature level must be 1, 2 or 3")
        return self.send("set_fan_temp", [level])

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


def _as_int(value: Any) -> int | None:
    """Convert a miIO scalar to int, returning None for unsupported values."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed in (1, 2, 3) else None
