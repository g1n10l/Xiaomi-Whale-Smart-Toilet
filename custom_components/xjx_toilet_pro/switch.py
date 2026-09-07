"""Switches for XJX Toilet Pro."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import ToiletlidStatus
from .const import CONF_MODEL, DEFAULT_NAME, DOMAIN, MODEL_XJX_TOILET_PRO
from .coordinator import XjxToiletProCoordinator
from .entity import XjxToiletProEntity


@dataclass(frozen=True, kw_only=True)
class XjxSwitchDescription(SwitchEntityDescription):
    """Describe an XJX switch."""

    value_fn: Callable[[ToiletlidStatus], bool]
    command_name: str


SWITCHES = (
    XjxSwitchDescription(
        key="led",
        translation_key="led",
        icon="mdi:led-on",
        value_fn=lambda status: status.led,
        command_name="set_led",
    ),
    XjxSwitchDescription(
        key="self_clean",
        translation_key="self_clean",
        icon="mdi:spray-bottle",
        value_fn=lambda status: status.self_clean,
        command_name="set_self_clean",
    ),
    XjxSwitchDescription(
        key="warm_air_drying",
        translation_key="warm_air_drying",
        icon="mdi:hair-dryer",
        value_fn=lambda status: status.warm_air_drying,
        command_name="set_warm_air_drying",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up switches from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: XjxToiletProCoordinator = data["coordinator"]
    mac: str = data["mac"]
    model = entry.data.get(CONF_MODEL, MODEL_XJX_TOILET_PRO)
    name = entry.title or DEFAULT_NAME
    async_add_entities(
        XjxToiletProSwitch(coordinator, desc, mac=mac, model=model, name=name)
        for desc in SWITCHES
    )


class XjxToiletProSwitch(XjxToiletProEntity, SwitchEntity):
    """Representation of a toilet-cover switch."""

    entity_description: XjxSwitchDescription

    def __init__(
        self,
        coordinator: XjxToiletProCoordinator,
        description: XjxSwitchDescription,
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
        """Return switch state."""
        if not self.coordinator.last_update_success or self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the feature on."""
        func = getattr(self.coordinator.client, self.entity_description.command_name)
        await self.coordinator.async_execute(func, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the feature off."""
        func = getattr(self.coordinator.client, self.entity_description.command_name)
        await self.coordinator.async_execute(func, False)
