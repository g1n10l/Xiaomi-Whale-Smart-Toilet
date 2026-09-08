"""DataUpdateCoordinator for XJX Toilet Pro."""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
import logging
from typing import Any

from miio import DeviceException

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ToiletlidStatus, XjxToiletProClient
from .const import DOMAIN, UPDATE_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class XjxToiletProCoordinator(DataUpdateCoordinator[ToiletlidStatus]):
    """Coordinate polling and commands for one toilet cover."""

    def __init__(self, hass: HomeAssistant, client: XjxToiletProClient) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )
        self.client = client
        self._estimated_states: dict[str, bool] = {}

    def estimated_state(self, key: str) -> bool:
        """Return an estimated feature state."""
        return self._estimated_states.get(key, False)

    @callback
    def async_set_estimated_state(self, key: str, state: bool) -> None:
        """Store an estimated state and notify entities."""
        self._estimated_states[key] = state
        self.async_update_listeners()

    async def _async_update_data(self) -> ToiletlidStatus:
        """Fetch state outside Home Assistant's event loop."""
        try:
            return await self.hass.async_add_executor_job(self.client.status)
        except DeviceException as err:
            raise UpdateFailed(
                f"Unable to communicate with the toilet cover: {err}"
            ) from err

    async def async_execute(
        self,
        func: Callable[..., Any],
        *args: Any,
        verify: Callable[[ToiletlidStatus], bool] | None = None,
    ) -> Any:
        """Run a blocking miIO command and refresh state."""
        try:
            result = await self.hass.async_add_executor_job(func, *args)
        except DeviceException as err:
            if verify is not None:
                await self.async_request_refresh()
                if (
                    self.last_update_success
                    and self.data is not None
                    and verify(self.data)
                ):
                    _LOGGER.debug(
                        "Device reported a command error, but it applied the state"
                    )
                    return None
            raise UpdateFailed(
                f"Unable to send command to the toilet cover: {err}"
            ) from err
        await self.async_request_refresh()
        return result
