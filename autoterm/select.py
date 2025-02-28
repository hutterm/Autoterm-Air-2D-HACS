"""Select Platform for AutoTerm Integration."""

from homeassistant.components.select import SelectEntity
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
    """Set up the Autoterm select platform."""
    device = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities([
        AutotermSelect(device, entry.entry_id)
    ])

class AutotermSelect(SelectEntity):
    """Representation of an Autoterm heater select entity."""

    _attr_name = "Select"
    _attr_unique_id = "select"
    _attr_device_info = {
        "identifiers": {(DOMAIN, entry_id)},
        "name": "Autoterm Air 2D",
        "manufacturer": MANUFACTURER,
        "model": MODEL,
        "sw_version": device.version,
    }
    _attr_options = ["Option 1", "Option 2", "Option 3"]
    _attr_current_option = "Option 1"

    def __init__(self, device, entry_id):
        """Initialize the select entity."""
        self._device = device
        self._entry_id = entry_id
        self._status_updated_signal = SIGNAL_STATE_UPDATED.format(f"{entry_id}_select")

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self._status_updated_signal, self.async_write_ha_state
            )
        )

    @property
    def state(self):
        """Return the state of the select."""
        return self._device.select
    
    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        self._device.select = option
        self.async_write_ha_state()

    @property
    def options(self):
        """Return the list of available options."""
        return self._attr_options
    
    @property
    def current_option(self):
        """Return the current selected option."""
        return self._attr_current_option
    
    @property
    def device_info(self):
        """Return device information."""
        return self._attr_device_info
    
    @property
    def icon(self):
        """Return the icon to display."""
        return self._attr_icon
    
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