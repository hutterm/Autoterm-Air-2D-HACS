"""Number Platform for AutoTerm."""
import logging

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODEL
from .device import SIGNAL_STATE_UPDATED

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Autoterm number platform."""
    device = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities([
        AutotermNumber(device, entry.entry_id)
    ])

class AutotermNumber(NumberEntity):
    """Representation of an Autoterm heater number entity."""

    _attr_name = "Number"
    _attr_unique_id = "number"
    _attr_device_info = {
        "identifiers": {(DOMAIN, entry_id)},
        "name": "Autoterm Air 2D",
        "manufacturer": MANUFACTURER,
        "model": MODEL,
        "sw_version": device.version,
    }
    _attr_min_value = 0
    _attr_max_value = 30
    _attr_step = 1
    _attr_value = 0

    def __init__(self, device, entry_id):
        """Initialize the number entity."""
        self._device = device
        self._entry_id = entry_id
        self._status_updated_signal = SIGNAL_STATE_UPDATED.format(f"{entry_id}_number")

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self._status_updated_signal, self.async_write_ha_state
            )
        )

    @property
    def state(self):
        """Return the state of the number."""
        return self._device.number
    
    async def async_set_value(self, value: float) -> None:
        """Set new value."""
        self._device.number = value
        self.async_write_ha_state()

    @property
    def value(self):
        """Return the value."""
        return self._device.number
    
    @property
    def min_value(self):
        """Return the minimum value."""
        return self._attr_min_value
    
    @property
    def max_value(self):
        """Return the maximum value."""
        return self._attr_max_value
    
    @property
    def step(self):
        """Return the step value."""
        return self._attr_step
    
    @property
    def device_info(self):
        """Return device information."""
        return self._attr_device_info
    
    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._attr_unique_id
    
    @property
    def should_poll(self) -> bool:
        """Disable polling."""
        return False
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._device.available
    
    async def async_update(self) -> None:
        """Update the entity."""
        await self._device.update()