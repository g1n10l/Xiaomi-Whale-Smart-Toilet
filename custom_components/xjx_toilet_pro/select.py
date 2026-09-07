"""Select entities for XJX Toilet Pro."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_MAC,
    CONF_MODEL,
    DATA_COORDINATOR,
    DEFAULT_NAME,
    DOMAIN,
    MODEL_XJX_TOILET_PRO,
)
from .coordinator import XjxToiletProCoordinator
from .entity import XjxToiletProEntity

TEMPERATURE_TO_LEVEL = {"low": 1, "medium": 2, "high": 3}
LEVEL_TO_TEMPERATURE = {
    level: option for option, level in TEMPERATURE_TO_LEVEL.items()
}

DESCRIPTION = SelectEntityDescription(
    key="fan_temperature",
    translation_key="fan_temperature",
    icon="mdi:heat-wave",
    options=list(TEMPERATURE_TO_LEVEL),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the warm-air temperature selector."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            XjxFanTemperatureSelect(
                data[DATA_COORDINATOR],
                mac=data[CONF_MAC],
                model=entry.data.get(CONF_MODEL, MODEL_XJX_TOILET_PRO),
                name=entry.title or DEFAULT_NAME,
            )
        ]
    )


class XjxFanTemperatureSelect(XjxToiletProEntity, SelectEntity):
    """Optimistic warm-air temperature selector."""

    entity_description = DESCRIPTION

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
            unique_suffix=DESCRIPTION.key,
        )
        self._selected_level: int | None = None

    @property
    def current_option(self) -> str | None:
        """Return the selected temperature level."""
        if self.coordinator.data is None:
            return None
        level = self.coordinator.data.fan_temperature or self._selected_level
        return LEVEL_TO_TEMPERATURE.get(level)

    async def async_select_option(self, option: str) -> None:
        """Set the warm-air temperature level."""
        level = TEMPERATURE_TO_LEVEL[option]
        await self.coordinator.async_execute(
            self.coordinator.client.set_fan_temperature, level
        )
        self._selected_level = level
        self.async_write_ha_state()
