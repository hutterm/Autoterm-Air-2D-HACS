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
from homeassistant.helpers import selector

from .const import DOMAIN, CONF_SERIAL_PORT, DEFAULT_NAME, ATTR_TEMPERATURE_ENTITY

_LOGGER = logging.getLogger(__name__)

class AutotermConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
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
        
        # Create more descriptive port options
        port_options = {}
        for port in ports:
            # Create a descriptive name that includes device info
            description = f"{port.device}"
            if port.name:
                description += f" - {port.name}"
            if port.description:
                description += f" - {port.description}"
            if port.manufacturer:
                description += f" ({port.manufacturer})"
            
                
            port_options[port.device] = description
        
        if user_input is not None:
            # Rest of your validation code remains unchanged
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
                    vol.Required(CONF_SERIAL_PORT): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(
                                    value=port.device,
                                    label=f"{port.device} - {port.name or 'Unknown'} - {port.description or 'Unknown'} ({port.manufacturer or 'Unknown'})"
                                )
                                for port in ports
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
        )
    
    # async def async_step_options(self, user_input=None):
    #     """Handle options flow."""
    #     if user_input is not None:
    #         return self.async_create_entry(title="", data=user_input)

    #     # Get all temperature sensor entities
    #     temperature_entities = []
    #     for entity_id in self.hass.states.async_entity_ids():
    #         state = self.hass.states.get(entity_id)
    #         if (
    #             state and 
    #             state.attributes.get("device_class") == "temperature" and
    #             entity_id.startswith("sensor.")
    #         ):
    #             temperature_entities.append(entity_id)

    #     return self.async_show_form(
    #         step_id="options",
    #         data_schema=vol.Schema({
    #             vol.Optional(ATTR_TEMPERATURE_ENTITY): vol.In(temperature_entities),
    #         }),
    #     )

    # def async_get_options_flow(config_entry):
    #     """Get the options flow for this handler."""
    #     return OptionsFlowHandler(config_entry)
    
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

# class OptionsFlowHandler(config_entries.OptionsFlow):
#     """Handle options flow for Autoterm integration."""

#     def __init__(self, config_entry):
#         """Initialize options flow."""
#         self.config_entry = config_entry

#     async def async_step_init(self, user_input=None):
#         """Manage the options."""
#         if user_input is not None:
#             return self.async_create_entry(title="", data=user_input)

#         # Get all temperature sensor entities
#         temperature_entities = []
#         for entity_id in self.hass.states.async_entity_ids():
#             state = self.hass.states.get(entity_id)
#             if (
#                 state and 
#                 state.attributes.get("device_class") == "temperature" and
#                 entity_id.startswith("sensor.")
#             ):
#                 temperature_entities.append(entity_id)

#         return self.async_show_form(
#             step_id="init",
#             data_schema=vol.Schema({
#                 vol.Optional(
#                     ATTR_TEMPERATURE_ENTITY,
#                     default=self.config_entry.options.get(
#                         ATTR_TEMPERATURE_ENTITY,
#                         self.config_entry.data.get(ATTR_TEMPERATURE_ENTITY, "")
#                     )
#                 ): vol.In(temperature_entities),
#             }),
#         )

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
