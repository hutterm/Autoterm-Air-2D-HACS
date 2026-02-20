"""Config flow for Autoterm integration."""

import logging
from typing import Any

import serial
import serial.tools.list_ports
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector

from .const import CONF_SERIAL_PORT, DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def _async_get_port_options(
    hass: HomeAssistant,
) -> list[selector.SelectOptionDict]:
    """Get list of available serial ports with descriptions."""
    ports = await hass.async_add_executor_job(serial.tools.list_ports.comports)
    return [
        selector.SelectOptionDict(
            value=port.device,
            label=f"{port.device} - {port.name or 'Unknown'} - {port.description or 'Unknown'} ({port.manufacturer or 'Unknown'})",
        )
        for port in ports
    ]


class AutotermConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Autoterm."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await self.hass.async_add_executor_job(
                    self._test_connection, user_input[CONF_SERIAL_PORT]
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=DEFAULT_NAME,
                    data=user_input,
                )

        port_options = await _async_get_port_options(self.hass)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SERIAL_PORT): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=port_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    def _test_connection(port: str) -> None:
        """Test if the port is available."""
        ser = None
        try:
            ser = serial.Serial(port, 9600, timeout=1)
        except serial.SerialException:
            raise CannotConnect
        finally:
            if ser:
                ser.close()

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Autoterm integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await self.hass.async_add_executor_job(
                    AutotermConfigFlow._test_connection, user_input[CONF_SERIAL_PORT]
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                new_data = {
                    **self.config_entry.data,
                    CONF_SERIAL_PORT: user_input[CONF_SERIAL_PORT],
                }
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=new_data
                )
                return self.async_create_entry(title="", data={})

        port_options = await _async_get_port_options(self.hass)
        current_port = self.config_entry.data.get(CONF_SERIAL_PORT, "")

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SERIAL_PORT, default=current_port
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=port_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
