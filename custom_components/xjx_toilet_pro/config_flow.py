"""Config flow for XJX Toilet Pro."""

from __future__ import annotations

import logging
from typing import Any

from miio import DeviceException
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import format_mac

from .api import XjxToiletProClient
from .const import CONF_MAC, CONF_MODEL, DEFAULT_NAME, DOMAIN, MODEL_XJX_TOILET_PRO

_LOGGER = logging.getLogger(__name__)


async def _validate_device(
    hass: HomeAssistant, host: str, token: str
) -> dict[str, str]:
    """Connect to the device and return identity information."""
    client = XjxToiletProClient(host, token)
    info = await hass.async_add_executor_job(client.info)
    model = info.model or MODEL_XJX_TOILET_PRO
    mac = format_mac(str(info.mac_address))
    return {CONF_MODEL: model, CONF_MAC: mac}


def _data_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return the connection form schema."""
    if defaults is None:
        return vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_TOKEN): vol.All(str, vol.Length(min=32, max=32)),
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            }
        )
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=defaults[CONF_HOST]): str,
            vol.Required(CONF_TOKEN, default=defaults[CONF_TOKEN]): vol.All(
                str, vol.Length(min=32, max=32)
            ),
            vol.Optional(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
        }
    )


class XjxToiletProConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for XJX Toilet Pro."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle manual setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            token = user_input[CONF_TOKEN].strip()
            try:
                info = await _validate_device(self.hass, host, token)
            except DeviceException:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error while validating XJX Toilet Pro")
                errors["base"] = "unknown"
            else:
                if info[CONF_MODEL] != MODEL_XJX_TOILET_PRO:
                    errors["base"] = "unsupported_model"
                else:
                    await self.async_set_unique_id(info[CONF_MAC])
                    self._abort_if_unique_id_configured(updates={CONF_HOST: host})
                    return self.async_create_entry(
                        title=user_input.get(CONF_NAME) or DEFAULT_NAME,
                        data={
                            CONF_HOST: host,
                            CONF_TOKEN: token,
                            CONF_NAME: user_input.get(CONF_NAME) or DEFAULT_NAME,
                            CONF_MODEL: info[CONF_MODEL],
                            CONF_MAC: info[CONF_MAC],
                        },
                    )

        return self.async_show_form(
            step_id="user", data_schema=_data_schema(), errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Allow changing the IP address, token, or display name."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            token = user_input[CONF_TOKEN].strip()
            try:
                info = await _validate_device(self.hass, host, token)
            except DeviceException:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error while reconfiguring XJX Toilet Pro")
                errors["base"] = "unknown"
            else:
                if info[CONF_MODEL] != MODEL_XJX_TOILET_PRO:
                    errors["base"] = "unsupported_model"
                else:
                    await self.async_set_unique_id(info[CONF_MAC])
                    self._abort_if_unique_id_mismatch()
                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates={
                            CONF_HOST: host,
                            CONF_TOKEN: token,
                            CONF_NAME: user_input.get(CONF_NAME) or DEFAULT_NAME,
                            CONF_MODEL: info[CONF_MODEL],
                            CONF_MAC: info[CONF_MAC],
                        },
                        title=user_input.get(CONF_NAME) or DEFAULT_NAME,
                    )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_data_schema(dict(entry.data)),
            errors=errors,
        )
