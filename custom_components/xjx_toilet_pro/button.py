"""Buttons for XJX Toilet Pro."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_MODEL,
    DATA_WATER_FILTER_TRACKER,
    DEFAULT_NAME,
    DOMAIN,
    MODEL_XJX_TOILET_PRO,
)
from .water_filter import WaterFilterTracker

DESCRIPTION = ButtonEntityDescription(
    key="water_filter_reset",
    translation_key="water_filter_reset",
    icon="mdi:restart",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the water-filter reset button."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            XjxWaterFilterResetButton(
                data[DATA_WATER_FILTER_TRACKER],
                mac=data["mac"],
                model=entry.data.get(CONF_MODEL, MODEL_XJX_TOILET_PRO),
                name=entry.title or DEFAULT_NAME,
            )
        ]
    )


class XjxWaterFilterResetButton(ButtonEntity):
    """Reset the water-filter replacement timestamp."""

    _attr_has_entity_name = True
    entity_description = DESCRIPTION

    def __init__(
        self, tracker: WaterFilterTracker, *, mac: str, model: str, name: str
    ) -> None:
        self._tracker = tracker
        self._attr_unique_id = f"{mac}_{DESCRIPTION.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac)},
            manufacturer="Xiaomi",
            model=model,
            name=name,
        )

    async def async_press(self) -> None:
        """Record the current time as the replacement time."""
        await self._tracker.async_reset()
