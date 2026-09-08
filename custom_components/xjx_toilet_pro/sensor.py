"""Sensors for XJX Toilet Pro."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
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

DESCRIPTION = SensorEntityDescription(
    key="water_filter_days_remaining",
    translation_key="water_filter_days_remaining",
    icon="mdi:water-sync",
    device_class=SensorDeviceClass.DURATION,
    native_unit_of_measurement=UnitOfTime.DAYS,
    state_class=SensorStateClass.MEASUREMENT,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the water-filter sensor."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            XjxWaterFilterSensor(
                data[DATA_COORDINATOR],
                mac=data[CONF_MAC],
                model=entry.data.get(CONF_MODEL, MODEL_XJX_TOILET_PRO),
                name=entry.title or DEFAULT_NAME,
            )
        ]
    )


class XjxWaterFilterSensor(XjxToiletProEntity, SensorEntity):
    """Number of days remaining for the water filter."""

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

    @property
    def native_value(self) -> int | None:
        """Return the decoded number of remaining days."""
        if not self.coordinator.last_update_success or self.coordinator.data is None:
            return None
        return self.coordinator.data.water_filter_days_remaining
