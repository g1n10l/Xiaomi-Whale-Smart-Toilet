"""Select entities for XJX Toilet Pro."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .api import DEFAULT_TEMPERATURE_LEVEL
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
LEVEL_TO_TEMPERATURE = {level: option for option, level in TEMPERATURE_TO_LEVEL.items()}


@dataclass(frozen=True, kw_only=True)
class XjxTemperatureDescription(SelectEntityDescription):
    """Describe an optimistic temperature selector."""

    command_name: str
    remember_command_name: str
    active_operation: str | None = None


TEMPERATURE_SELECTS = (
    XjxTemperatureDescription(
        key="fan_temperature",
        translation_key="fan_temperature",
        icon="mdi:heat-wave",
        options=list(TEMPERATURE_TO_LEVEL),
        command_name="set_fan_temperature",
        remember_command_name="remember_fan_temperature",
        active_operation="warm_air_drying",
    ),
    XjxTemperatureDescription(
        key="rear_wash_water_temperature",
        translation_key="rear_wash_water_temperature",
        icon="mdi:thermometer-water",
        options=list(TEMPERATURE_TO_LEVEL),
        command_name="set_rear_wash_water_temperature",
        remember_command_name="remember_rear_wash_water_temperature",
        active_operation="rear_wash",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up temperature selectors."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            XjxTemperatureSelect(
                data[DATA_COORDINATOR],
                description,
                mac=data[CONF_MAC],
                model=entry.data.get(CONF_MODEL, MODEL_XJX_TOILET_PRO),
                name=entry.title or DEFAULT_NAME,
            )
            for description in TEMPERATURE_SELECTS
        ]
    )


class XjxTemperatureSelect(XjxToiletProEntity, SelectEntity, RestoreEntity):
    """Optimistic temperature selector with restored state."""

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
        self._selected_level = DEFAULT_TEMPERATURE_LEVEL

    async def async_added_to_hass(self) -> None:
        """Restore the last selected temperature."""
        await super().async_added_to_hass()
        if (
            last_state := await self.async_get_last_state()
        ) is not None and last_state.state in TEMPERATURE_TO_LEVEL:
            self._selected_level = TEMPERATURE_TO_LEVEL[last_state.state]
            remember = getattr(
                self.coordinator.client,
                self.entity_description.remember_command_name,
            )
            remember(self._selected_level)

    @property
    def current_option(self) -> str | None:
        """Return the selected temperature level."""
        return LEVEL_TO_TEMPERATURE[self._selected_level]

    async def async_select_option(self, option: str) -> None:
        """Set the temperature level."""
        level = TEMPERATURE_TO_LEVEL[option]
        remember = getattr(
            self.coordinator.client,
            self.entity_description.remember_command_name,
        )
        remember(level)
        self._selected_level = level
        self.async_write_ha_state()

        active_operation = self.entity_description.active_operation
        if active_operation and not self.coordinator.estimated_state(active_operation):
            return

        command = getattr(
            self.coordinator.client,
            self.entity_description.command_name,
        )
        await self.coordinator.async_execute(command, level)
