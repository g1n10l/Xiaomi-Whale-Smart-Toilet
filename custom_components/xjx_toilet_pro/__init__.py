"""XJX Toilet Pro integration."""

from __future__ import annotations

import ast
from typing import Any

from miio import DeviceException
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import (
    ConfigEntryNotReady,
    HomeAssistantError,
    ServiceValidationError,
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .api import XjxToiletProClient
from .const import (
    ATTR_COMMAND,
    ATTR_PARAMS,
    CONF_MAC,
    CONF_MODEL,
    DATA_COORDINATOR,
    DOMAIN,
    MODEL_XJX_TOILET_PRO,
    SERVICE_SEND_COMMAND,
)
from .coordinator import XjxToiletProCoordinator

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SERVICE_SEND_COMMAND_SCHEMA = vol.Schema(
    {
        vol.Required("config_entry_id"): cv.string,
        vol.Required(ATTR_COMMAND): cv.string,
        vol.Optional(ATTR_PARAMS): vol.Any(dict, cv.ensure_list, None),
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up integration-level services."""

    async def async_send_command(call: ServiceCall) -> None:
        entry_id = call.data["config_entry_id"]
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is None or entry.domain != DOMAIN:
            raise ServiceValidationError("XJX Toilet Pro config entry not found")
        if entry_id not in hass.data.get(DOMAIN, {}):
            raise ServiceValidationError("XJX Toilet Pro config entry is not loaded")

        coordinator: XjxToiletProCoordinator = hass.data[DOMAIN][entry_id][
            DATA_COORDINATOR
        ]
        params: Any = call.data.get(ATTR_PARAMS)
        # Older automations may pass a list literal as a string.
        if isinstance(params, list) and len(params) == 1 and isinstance(params[0], str):
            text = params[0].strip()
            if text.startswith("[") and text.endswith("]"):
                try:
                    parsed = ast.literal_eval(text)
                except (SyntaxError, ValueError):
                    pass
                else:
                    if isinstance(parsed, list):
                        params = parsed
            elif text.isnumeric():
                params = [int(text)]

        try:
            await coordinator.async_execute(
                coordinator.client.raw_command,
                call.data[ATTR_COMMAND],
                params,
            )
        except Exception as err:
            raise HomeAssistantError(f"Unable to send raw command: {err}") from err

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_COMMAND,
        async_send_command,
        schema=SERVICE_SEND_COMMAND_SCHEMA,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up XJX Toilet Pro from a config entry."""
    host = entry.data[CONF_HOST]
    token = entry.data[CONF_TOKEN]
    model = entry.data.get(CONF_MODEL, MODEL_XJX_TOILET_PRO)
    client = XjxToiletProClient(host, token, model=model)

    try:
        info = await hass.async_add_executor_job(client.info)
    except DeviceException as err:
        raise ConfigEntryNotReady(f"Unable to connect to {host}: {err}") from err

    mac = str(entry.data.get(CONF_MAC) or info.mac_address).lower()
    coordinator = XjxToiletProCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
        CONF_MAC: mac,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
