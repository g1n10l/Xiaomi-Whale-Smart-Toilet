"""Binary sensors for XJX Toilet Pro."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import ToiletlidStatus
from .const import CONF_MODEL, DEFAULT_NAME, DOMAIN, MODEL_XJX_TOILET_PRO
from .coordinator import XjxToiletProCoordinator
from .entity import XjxToiletProEntity


@dataclass(frozen=True, kw_only=True)
class XjxBinarySensorDescription(BinarySensorEntityDescription):
    """Describe an XJX binary sensor."""

    value_fn: Callable[[ToiletlidStatus], bool]


SENSORS = (
    XjxBinarySensorDescription(
        key="occupied",
        translation_key="occupied",
        icon="mdi:toilet",
        device_class=BinarySensorDeviceClass.OCCUPANCY,
        value_fn=lambda status: status.seating,
    ),
    XjxBinarySensorDescription(
        key="air_filter",
        translation_key="air_filter",
        icon="mdi:air-filter",
        value_fn=lambda status: status.air_filter,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up binary sensors from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: XjxToiletProCoordinator = data["coordinator"]
    mac: str = data["mac"]
    model = entry.data.get(CONF_MODEL, MODEL_XJX_TOILET_PRO)
    name = entry.title or DEFAULT_NAME
    async_add_entities(
        XjxToiletProBinarySensor(coordinator, desc, mac=mac, model=model, name=name)
        for desc in SENSORS
    )


class XjxToiletProBinarySensor(XjxToiletProEntity, BinarySensorEntity):
    """Representation of a toilet-cover binary sensor."""

    entity_description: XjxBinarySensorDescription

    def __init__(
        self,
        coordinator: XjxToiletProCoordinator,
        description: XjxBinarySensorDescription,
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

    @property
    def is_on(self) -> bool | None:
        """Return the binary state."""
        if not self.coordinator.last_update_success or self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
