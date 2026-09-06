"""DataUpdateCoordinator for XJX Toilet Pro."""

from __future__ import annotations

from datetime import timedelta
from functools import partial
import logging
from typing import Any
from collections.abc import Callable

from miio import DeviceException

from homeassistant.core import HomeAssistant
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

    async def _async_update_data(self) -> ToiletlidStatus:
        """Fetch state outside Home Assistant's event loop."""
        try:
            return await self.hass.async_add_executor_job(self.client.status)
        except DeviceException as err:
            raise UpdateFailed(
                f"Unable to communicate with the toilet cover: {err}"
            ) from err

    async def async_execute(self, func: Callable[..., Any], *args: Any) -> Any:
        """Run a blocking miIO command and refresh state."""
        try:
            result = await self.hass.async_add_executor_job(partial(func, *args))
        except DeviceException as err:
            raise UpdateFailed(
                f"Unable to send command to the toilet cover: {err}"
            ) from err
        await self.async_request_refresh()
        return result
