"""Switches for XJX Toilet Pro."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_call_later

from .api import ToiletlidStatus
from .const import (
    CONF_MAC,
    CONF_MODEL,
    DATA_COORDINATOR,
    DEFAULT_NAME,
    DOMAIN,
    INACTIVE_SWITCH_RESET_SECONDS,
    MODEL_XJX_TOILET_PRO,
    WARM_AIR_DRYING_DURATION_SECONDS,
)
from .coordinator import XjxToiletProCoordinator
from .entity import XjxToiletProEntity


@dataclass(frozen=True, kw_only=True)
class XjxSwitchDescription(SwitchEntityDescription):
    """Describe an XJX switch."""

    value_fn: Callable[[ToiletlidStatus], bool] | None = None
    command_name: str
    optimistic: bool = False
    estimated_duration: int | None = None


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
        command_name="set_warm_air_drying",
        optimistic=True,
        estimated_duration=WARM_AIR_DRYING_DURATION_SECONDS,
    ),
    XjxSwitchDescription(
        key="rear_wash",
        translation_key="rear_wash",
        icon="mdi:shower-head",
        command_name="set_rear_wash",
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
        self._cancel_inactive_reset: Callable[[], None] | None = None
        self._cancel_estimated_stop: Callable[[], None] | None = None

    @property
    def is_on(self) -> bool | None:
        """Return switch state."""
        if self.entity_description.optimistic:
            return self.coordinator.estimated_state(self.entity_description.key)
        if not self.coordinator.last_update_success or self.coordinator.data is None:
            return None
        value_fn = self.entity_description.value_fn
        return value_fn(self.coordinator.data) if value_fn is not None else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the feature on."""
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the feature off."""
        await self._async_set_state(False)

    async def async_will_remove_from_hass(self) -> None:
        """Cancel a pending inactive-seat check before removal."""
        self._cancel_pending_resets()
        await super().async_will_remove_from_hass()

    async def _async_set_state(self, state: bool) -> None:
        """Set and verify the switch state."""
        func = getattr(self.coordinator.client, self.entity_description.command_name)
        value_fn = self.entity_description.value_fn
        await self.coordinator.async_execute(
            func,
            state,
            verify=(
                None
                if self.entity_description.optimistic
                else lambda status: value_fn is not None and value_fn(status) is state
            ),
        )
        if self.entity_description.optimistic:
            self._cancel_pending_resets()
            self.coordinator.async_set_estimated_state(
                self.entity_description.key, state
            )
            if state:
                self._cancel_inactive_reset = async_call_later(
                    self.hass,
                    INACTIVE_SWITCH_RESET_SECONDS,
                    self._reset_if_unoccupied,
                )
                if duration := self.entity_description.estimated_duration:
                    self._cancel_estimated_stop = async_call_later(
                        self.hass,
                        duration,
                        self._stop_estimate,
                    )

    @callback
    def _reset_if_unoccupied(self, _now: Any) -> None:
        """Reset the displayed state when the seat remains unoccupied."""
        self._cancel_inactive_reset = None
        status = self.coordinator.data
        if status is None or not status.seating:
            if self._cancel_estimated_stop is not None:
                self._cancel_estimated_stop()
                self._cancel_estimated_stop = None
            self.coordinator.async_set_estimated_state(
                self.entity_description.key, False
            )

    @callback
    def _stop_estimate(self, _now: Any) -> None:
        """Mark an estimated feature as stopped."""
        self._cancel_estimated_stop = None
        self.coordinator.async_set_estimated_state(
            self.entity_description.key, False
        )

    def _cancel_pending_resets(self) -> None:
        """Cancel pending estimated-state resets."""
        if self._cancel_inactive_reset is not None:
            self._cancel_inactive_reset()
            self._cancel_inactive_reset = None
        if self._cancel_estimated_stop is not None:
            self._cancel_estimated_stop()
            self._cancel_estimated_stop = None
