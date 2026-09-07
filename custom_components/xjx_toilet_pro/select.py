"""Select entities for XJX Toilet Pro."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_MODEL, DEFAULT_NAME, DOMAIN, MODEL_XJX_TOILET_PRO
from .coordinator import XjxToiletProCoordinator
from .entity import XjxToiletProEntity

TEMPERATURE_TO_LEVEL = {"low": 1, "medium": 2, "high": 3}
LEVEL_TO_TEMPERATURE = {
    level: option for option, level in TEMPERATURE_TO_LEVEL.items()
}


@dataclass(frozen=True, kw_only=True)
class XjxTemperatureDescription(SelectEntityDescription):
    """Describe an XJX temperature selector."""

    status_attribute: str
    command_name: str


TEMPERATURE_SELECTS = (
    XjxTemperatureDescription(
        key="fan_temperature",
        translation_key="fan_temperature",
        icon="mdi:heat-wave",
        options=list(TEMPERATURE_TO_LEVEL),
        status_attribute="fan_temperature",
        command_name="set_fan_temperature",
    ),
    XjxTemperatureDescription(
        key="rear_wash_water_temperature",
        translation_key="rear_wash_water_temperature",
        icon="mdi:thermometer-water",
        options=list(TEMPERATURE_TO_LEVEL),
        status_attribute="rear_wash_water_temperature",
        command_name="set_rear_wash_water_temperature",
    ),
    XjxTemperatureDescription(
        key="feminine_wash_water_temperature",
        translation_key="feminine_wash_water_temperature",
        icon="mdi:thermometer-water",
        options=list(TEMPERATURE_TO_LEVEL),
        status_attribute="feminine_wash_water_temperature",
        command_name="set_feminine_wash_water_temperature",
    ),
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
        XjxTemperatureSelect(
            coordinator,
            description,
            mac=mac,
            model=model,
            name=name,
        )
        for description in TEMPERATURE_SELECTS
    )


class XjxTemperatureSelect(XjxToiletProEntity, SelectEntity):
    """Optimistic temperature-level selector."""

    entity_description: XjxTemperatureDescription

    def __init__(
        self,
        coordinator: XjxToiletProCoordinator,
        description: XjxTemperatureDescription,
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
            unique_suffix=description.key,
        )
        self.entity_description = description
        self._selected_level: int | None = None

    @property
    def current_option(self) -> str | None:
        """Return the selected temperature level."""
        if self.coordinator.data is None:
            return None
        level = (
            getattr(self.coordinator.data, self.entity_description.status_attribute)
            or self._selected_level
        )
        return LEVEL_TO_TEMPERATURE.get(level)

    async def async_select_option(self, option: str) -> None:
        """Set the temperature level."""
        level = TEMPERATURE_TO_LEVEL[option]
        func = getattr(self.coordinator.client, self.entity_description.command_name)
        await self.coordinator.async_execute(func, level)
        self._selected_level = level
        self.async_write_ha_state()
