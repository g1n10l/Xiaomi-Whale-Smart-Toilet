"""Sensors for XJX Toilet Pro."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
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

DESCRIPTION = SensorEntityDescription(
    key="water_filter_last_replaced",
    translation_key="water_filter_last_replaced",
    device_class=SensorDeviceClass.TIMESTAMP,
    icon="mdi:water-sync",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the water-filter replacement sensor."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            XjxWaterFilterLastReplacedSensor(
                data[DATA_WATER_FILTER_TRACKER],
                mac=data["mac"],
                model=entry.data.get(CONF_MODEL, MODEL_XJX_TOILET_PRO),
                name=entry.title or DEFAULT_NAME,
            )
        ]
    )


class XjxWaterFilterLastReplacedSensor(SensorEntity):
    """Show when the water filter was last replaced."""

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

    async def async_added_to_hass(self) -> None:
        """Subscribe to replacement-time updates."""
        await super().async_added_to_hass()
        self.async_on_remove(self._tracker.async_add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self) -> datetime | None:
        """Return the last replacement timestamp."""
        return self._tracker.last_replaced
