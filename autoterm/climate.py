"""Climate platform for Autoterm integration."""
import logging
from typing import Any, Callable, Dict, List, Optional

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    HVACAction,
)
from homeassistant.components.climate.const import UnitOfTemperature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODEL
from .device import SIGNAL_STATE_UPDATED

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Autoterm climate platform."""
    device = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities([
        AutotermClimate(device, entry.entry_id)
    ])

class AutotermClimate(ClimateEntity):
    """Representation of an Autoterm heater climate entity."""

    _attr_has_entity_name = True
    _attr_name = "Climate"
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
    )
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.FAN_ONLY]
    _attr_min_temp = 0
    _attr_max_temp = 30
    _attr_target_temperature_step = 1
    
    def __init__(self, device, entry_id):
        """Initialize the climate entity."""
        self._device = device
        self._entry_id = entry_id
        self._attr_unique_id = f"{entry_id}_climate"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "Autoterm Air 2D",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "sw_version": device.version,
        }
        self._status_updated_signal = SIGNAL_STATE_UPDATED.format(f"{entry_id}_control")
        self._temperature_updated_signal = SIGNAL_STATE_UPDATED.format(f"{entry_id}_temperature_target")
        
    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self._status_updated_signal, self.async_write_ha_state
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self._temperature_updated_signal, self.async_write_ha_state
            )
        )
        
    @property
    def hvac_mode(self) -> HVACMode:
        """Return current operation."""
        control = self._device.get_entity_state("control")
        if control == "Aus":
            return HVACMode.OFF
        elif control == "Nur Ventilator":
            return HVACMode.FAN_ONLY
        return HVACMode.HEAT
        
    @property