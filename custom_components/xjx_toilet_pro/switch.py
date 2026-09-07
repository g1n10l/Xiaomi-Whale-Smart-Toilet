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
class XjxSwitchDescription(SwitchEntityDescription):
    """Describe an XJX switch."""

    value_fn: Callable[[ToiletlidStatus], bool | None]
    command_name: str
    optimistic: bool = False


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
        optimistic=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up switches from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: XjxToiletProCoordinator = data[DATA_COORDINATOR]
    mac: str = data[CONF_MAC]
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
        self._optimistic_state: bool | None = None

    @property
    def is_on(self) -> bool | None:
        """Return switch state."""
        if not self.coordinator.last_update_success or self.coordinator.data is None:
            return None
        state = self.entity_description.value_fn(self.coordinator.data)
        return self._optimistic_state if state is None else state

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the feature on."""
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the feature off."""
        await self._async_set_state(False)

    async def _async_set_state(self, state: bool) -> None:
        """Set and verify the switch state."""
        func = getattr(self.coordinator.client, self.entity_description.command_name)
        await self.coordinator.async_execute(
            func,
            state,
            verify=(
                None
                if self.entity_description.optimistic
                else lambda status: self.entity_description.value_fn(status) is state
            ),
        )
        if self.entity_description.optimistic:
            self._optimistic_state = state
            self.async_write_ha_state()
