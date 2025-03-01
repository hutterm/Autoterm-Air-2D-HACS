"""The Autoterm Heater integration."""
import asyncio
import logging
from datetime import timedelta

import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import service

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.event import async_track_time_interval
import async_timeout

from .const import DOMAIN, CONF_SERIAL_PORT, ATTR_TEMPERATURE_ENTITY, SERVICE_UPDATE_TEMPERATURE
from .device import AutotermDevice

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.CLIMATE,
    Platform.SENSOR,
    Platform.SELECT,
    Platform.NUMBER,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Autoterm from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    device = AutotermDevice(
        hass,
        entry.data[CONF_SERIAL_PORT],
        hass.loop,
        entry.entry_id
    )
    
    try:
        await device.connect()
    except Exception as ex:
        _LOGGER.error(f"Failed to connect to Autoterm device: {ex}")
        return False
    

    # # Create update coordinator
    # async def async_update_data():
    #     """Fetch data from the device."""
    #     try:
    #         async with async_timeout.timeout(10):  # 10 second timeout for device communication
    #             # Poll for status
    #             await device.send_message('status')
    #             await asyncio.sleep(0.5)  # Small delay between messages
    #             await device.send_message('settings')
                
    #             return {
    #                 "status": device.status_data,
    #                 "settings": device.settings_data
    #             }
    #     except Exception as err:
    #         raise UpdateFailed(f"Error communicating with Autoterm device: {err}")
    
    # coordinator = DataUpdateCoordinator(
    #     hass,
    #     _LOGGER,
    #     name="autoterm",
    #     update_method=async_update_data,
    #     update_interval=timedelta(seconds=30),  # Adjust polling interval as needed
    # )
    
    # # Do an initial data update
    # await coordinator.async_config_entry_first_refresh()

    # # Store both the device and coordinator in hass data
    # hass.data.setdefault(DOMAIN, {})
    # hass.data[DOMAIN][entry.entry_id] = {
    #     "device": device,
    #     "coordinator": coordinator
    # }
    hass.data[DOMAIN][entry.entry_id] = device

    # Register service for manual temperature update
    async def handle_update_temperature(call):
        """Handle the service call to update temperature."""
        device = hass.data[DOMAIN][entry.entry_id]
        temp_entity_id = call.data.get(ATTR_TEMPERATURE_ENTITY)
        
        if temp_entity_id:
            temp_state = hass.states.get(temp_entity_id)
            if temp_state:
                try:
                    temp_value = float(temp_state.state)
                    # Round to nearest integer as your device expects integer values
                    await device.set_temperature_current(round(temp_value))
                    _LOGGER.info(f"Updated heater with temperature {temp_value} from {temp_entity_id}")
                except (ValueError, TypeError):
                    _LOGGER.error(f"Invalid temperature value from {temp_entity_id}: {temp_state.state}")
            else:
                _LOGGER.error(f"Temperature entity {temp_entity_id} not found")
    
    hass.services.async_register(
        DOMAIN, 
        SERVICE_UPDATE_TEMPERATURE, 
        handle_update_temperature,
        schema=vol.Schema({
            vol.Required(ATTR_TEMPERATURE_ENTITY): vol.All(cv.ensure_list, [cv.entity_id]),
        })
    )

    # Now set up the periodic update if a temperature entity is configured
    temp_entity_id = entry.options.get(ATTR_TEMPERATURE_ENTITY, entry.data.get(ATTR_TEMPERATURE_ENTITY))
    
    if temp_entity_id:
        async def periodic_temp_update(now=None):
            """Update the temperature periodically."""
            await handle_update_temperature(service.ServiceCall(
                DOMAIN, 
                SERVICE_UPDATE_TEMPERATURE, 
                {ATTR_TEMPERATURE_ENTITY: temp_entity_id}
            ))
        
        # Update initially
        await periodic_temp_update()
        
        # Schedule updates every 60 seconds (adjust as needed)
        entry.async_on_unload(
            async_track_time_interval(
                hass, 
                periodic_temp_update, 
                timedelta(seconds=60)
            )
        )


    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(update_listener))
    
 
    

    # Set up periodic status polling
    async def periodic_status_poll(now=None):
        """Poll the device status periodically."""
        device = hass.data[DOMAIN][entry.entry_id]
        try:
            await device.send_message('status')
            await asyncio.sleep(0.5)  # Small delay between messages
            await device.send_message('settings')
        except Exception as ex:
            _LOGGER.error(f"Error polling device status: {ex}")

    # Schedule status polling every 30 seconds (adjust as needed)
    entry.async_on_unload(
        async_track_time_interval(
            hass,
            periodic_status_poll,
            timedelta(seconds=30)
        )
    )


    # entry.async_on_unload(
    #     entry.add_update_listener(async_reload_entry)
    # )
    
    return True

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        device = hass.data[DOMAIN].pop(entry.entry_id)
        await device.disconnect()
    
    return unload_ok

