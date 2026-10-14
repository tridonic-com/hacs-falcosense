"""Config flow for the Tridonic FalcoSENSE integration."""

from collections.abc import Mapping
from typing import Any, override

from falcosense import FalcoSense, FalcoSenseAuthError, FalcoSenseConnectionError
import probatio

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_TOKEN
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_OVERLAY, DOMAIN

STEP_USER_DATA_SCHEMA = probatio.Schema(
    {
        probatio.Required(CONF_HOST): str,
        probatio.Required(CONF_TOKEN): str,
    }
)

STEP_REAUTH_DATA_SCHEMA = probatio.Schema({probatio.Required(CONF_TOKEN): str})


class FalcoSenseConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tridonic FalcoSENSE."""

    @staticmethod
    @callback
    @override
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> FalcoSenseOptionsFlow:
        """Return the options flow."""
        return FalcoSenseOptionsFlow()

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            client = FalcoSense(
                user_input[CONF_HOST],
                user_input[CONF_TOKEN],
                async_get_clientsession(self.hass, verify_ssl=False),
            )
            try:
                device_name = await client.async_validate()
            except FalcoSenseAuthError:
                errors["base"] = "invalid_auth"
            except FalcoSenseConnectionError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(device_name)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=device_name, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle re-authentication when the token is rejected."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm re-authentication with a new token."""
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()
        if user_input is not None:
            client = FalcoSense(
                reauth_entry.data[CONF_HOST],
                user_input[CONF_TOKEN],
                async_get_clientsession(self.hass, verify_ssl=False),
            )
            try:
                device_name = await client.async_validate()
            except FalcoSenseAuthError:
                errors["base"] = "invalid_auth"
            except FalcoSenseConnectionError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(device_name)
                self._abort_if_unique_id_mismatch(reason="wrong_device")
                return self.async_update_reload_and_abort(
                    reauth_entry, data_updates=user_input
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_REAUTH_DATA_SCHEMA,
            errors=errors,
        )


class FalcoSenseOptionsFlow(OptionsFlow):
    """Handle options for Tridonic FalcoSENSE."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=probatio.Schema(
                {
                    probatio.Required(
                        CONF_OVERLAY,
                        default=self.config_entry.options.get(CONF_OVERLAY, True),
                    ): bool,
                }
            ),
        )
