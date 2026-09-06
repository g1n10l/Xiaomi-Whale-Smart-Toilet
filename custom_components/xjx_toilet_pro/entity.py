"""Base entity for XJX Toilet Pro."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import XjxToiletProCoordinator


class XjxToiletProEntity(CoordinatorEntity[XjxToiletProCoordinator]):
    """Common entity attributes."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: XjxToiletProCoordinator,
        *,
        mac: str,
        model: str,
        name: str,
        unique_suffix: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{mac}_{unique_suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac)},
            manufacturer="Xiaomi",
            model=model,
            name=name,
        )
