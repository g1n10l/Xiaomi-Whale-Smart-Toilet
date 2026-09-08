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

from .api import ToiletLidStatus
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


@dataclass(frozen=True, kw_only=True)
class XjxBinarySensorDescription(BinarySensorEntityDescription):
    """Describe an XJX binary sensor."""

    value_fn: Callable[[ToiletLidStatus], bool] | None = None
    estimated_key: str | None = None


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
    XjxBinarySensorDescription(
        key="warm_air_drying_status",
        translation_key="warm_air_drying_status",
        icon="mdi:hair-dryer",
        device_class=BinarySensorDeviceClass.RUNNING,
        estimated_key="warm_air_drying",
    ),
    XjxBinarySensorDescription(
        key="rear_wash_status",
        translation_key="rear_wash_status",
        icon="mdi:shower-head",
        device_class=BinarySensorDeviceClass.RUNNING,
        estimated_key="rear_wash",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up binary sensors from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: XjxToiletProCoordinator = data[DATA_COORDINATOR]
    mac: str = data[CONF_MAC]
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
        if self.entity_description.estimated_key is not None:
            return self.coordinator.estimated_state(
                self.entity_description.estimated_key
            )
        if not self.coordinator.last_update_success or self.coordinator.data is None:
            return None
        value_fn = self.entity_description.value_fn
        return value_fn(self.coordinator.data) if value_fn is not None else None
