import logging
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_PORT
from .autoterm import AutotermHeater

DOMAIN = "autoterm"
_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema({
            vol.Required(CONF_PORT): str
        })
    },
    extra=vol.ALLOW_EXTRA,
)

def setup(hass: HomeAssistant, config: dict):
    """Set up the Autoterm integration."""
    port = config[DOMAIN].get(CONF_PORT)
    
    heater = AutotermHeater(port)
    heater.connect()
    hass.data[DOMAIN] = heater
    
    return True

def unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload the Autoterm integration."""
    heater = hass.data.pop(DOMAIN, None)
    if heater:
        heater.disconnect()
    return True