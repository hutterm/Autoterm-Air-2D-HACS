"""Config flow for Autoterm integration."""
import logging
from typing import Any

import serial
import serial.tools.list_ports
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, CONF_SERIAL_PORT, DEFAULT_NAME

_LOGGER = logging.getLogger(__name__)

class AutotermFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Autoterm."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        ports = await self.hass.async_add_executor_job(
            serial.tools.list_ports.comports
        )
        port_names = [port.device for port in ports]
        
        if user_input is not None:
            # Validate the port
            try:
                await self.hass.async_add_executor_job(
                    self._test_connection, user_input[CONF_SERIAL_PORT]
                )
                return self.async_create_entry(
                    title=DEFAULT_NAME,
                    data=user_input,
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SERIAL_PORT): vol.In(port_names),
                }
            ),
            errors=errors,
        )

    @staticmethod
    def _test_connection(port: str) -> None:
        """Test if the port is available."""
        try:
            ser = serial.Serial(port, 9600, timeout=1)
            ser.close()
        except serial.SerialException:
            raise CannotConnect

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
