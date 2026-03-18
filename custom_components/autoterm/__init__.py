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

    async def _resubmit_cached_external_temperature(
        current_device: AutotermDevice, temp_entity_id: str, reason: str
    ) -> None:
        """Resubmit the last known valid external temperature if available."""
        if await current_device.submit_cached_external_temperature():
            _LOGGER.debug(
                "Resubmitted cached external temperature because %s for %s",
                reason,
                temp_entity_id,
            )

    async def periodic_temp_update(now=None):
        """Update the temperature periodically."""
        current_device: AutotermDevice = hass.data[DOMAIN][entry.entry_id]
        temp_entity_id = current_device.get_external_temperature_sensor()
        if not temp_entity_id:
            return

        temp_state = hass.states.get(temp_entity_id)
        if not temp_state:
            _LOGGER.debug("Temperature entity %s not found", temp_entity_id)
            await _resubmit_cached_external_temperature(
                current_device, temp_entity_id, "sensor entity was not found"
            )
            return

        if temp_state.state in ("unknown", "unavailable"):
            _LOGGER.debug(
                "Temperature entity %s has non-numeric state %s",
                temp_entity_id,
                temp_state.state,
            )
            await _resubmit_cached_external_temperature(
                current_device,
                temp_entity_id,
                f"state is {temp_state.state}",
            )
            return

        try:
            temp_value = float(temp_state.state)
        except (ValueError, TypeError):
            _LOGGER.debug(
                "Temperature entity %s has invalid numeric value %s",
                temp_entity_id,
                temp_state.state,
            )
            await _resubmit_cached_external_temperature(
                current_device,
                temp_entity_id,
                "state is not numeric",
            )
            return

        await current_device.submit_external_temperature(temp_value)
        _LOGGER.debug(
            "Updated heater with temperature %.2f from %s",
            temp_value,
            temp_entity_id,
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))

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
            timedelta(seconds=5)
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

