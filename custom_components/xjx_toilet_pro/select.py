"""Select entities for XJX Toilet Pro."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_MODEL, DEFAULT_NAME, DOMAIN, MODEL_XJX_TOILET_PRO
from .coordinator import XjxToiletProCoordinator
from .entity import XjxToiletProEntity

FAN_TEMPERATURE_TO_LEVEL = {
    "low": 1,
    "medium": 2,
    "high": 3,
}
LEVEL_TO_FAN_TEMPERATURE = {
    level: option for option, level in FAN_TEMPERATURE_TO_LEVEL.items()
}

FAN_TEMPERATURE_DESCRIPTION = SelectEntityDescription(
    key="fan_temperature",
    translation_key="fan_temperature",
    icon="mdi:heat-wave",
    options=list(FAN_TEMPERATURE_TO_LEVEL),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up selects from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: XjxToiletProCoordinator = data["coordinator"]
    mac: str = data["mac"]
    model = entry.data.get(CONF_MODEL, MODEL_XJX_TOILET_PRO)
    name = entry.title or DEFAULT_NAME
    async_add_entities(
        [
            XjxFanTemperatureSelect(
                coordinator,
                mac=mac,
                model=model,
                name=name,
            )
        ]
    )


class XjxFanTemperatureSelect(XjxToiletProEntity, SelectEntity):
    """Warm-air drying temperature selector."""

    entity_description = FAN_TEMPERATURE_DESCRIPTION

    def __init__(
        self,
        coordinator: XjxToiletProCoordinator,
        *,
        mac: str,
        model: str,
        name: str,
    ) -> None:
        super().__init__(
            coordinator,
            mac=mac,
            model=model,
            name=name,
            unique_suffix="fan_temperature",
        )
        self._selected_level: int | None = None

    @property
    def current_option(self) -> str | None:
        """Return the selected warm-air temperature."""
        if self.coordinator.data is None:
            return None
        level = self.coordinator.data.fan_temperature or self._selected_level
        return LEVEL_TO_FAN_TEMPERATURE.get(level)

    async def async_select_option(self, option: str) -> None:
        """Set the warm-air temperature."""
        level = FAN_TEMPERATURE_TO_LEVEL[option]
        await self.coordinator.async_execute(
            self.coordinator.client.set_fan_temperature,
            level,
        )
        self._selected_level = level
        self.async_write_ha_state()
