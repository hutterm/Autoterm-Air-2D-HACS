"""The Autoterm Heater integration."""
import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN, CONF_SERIAL_PORT
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
        entry.data[CONF_SERIAL_PORT],
        hass.loop,
        entry.entry_id
    )
    
    try:
        await device.connect()
    except Exception as ex:
        _LOGGER.error(f"Failed to connect to Autoterm device: {ex}")
        return False
    
    hass.data[DOMAIN][entry.entry_id] = device
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    entry.async_on_unload(entry.add_update_listener(update_listener))
    
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
