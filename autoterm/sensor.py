"""Sensor Platform for AutoTerm Integration."""

from homeassistant.helpers.entity import Entity
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
    """Set up the Autoterm sensor platform."""
    device = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities([
        AutotermSensor(device, entry.entry_id)
    ])

class AutotermSensor(Entity):
    """Representation of an Autoterm heater sensor entity."""

    _attr_name = "Sensor"
    _attr_unique_id = "sensor"
    _attr_device_info = {
        "identifiers": {(DOMAIN, entry_id)},
        "name": "Autoterm Air 2D",
        "manufacturer": MANUFACTURER,
        "model": MODEL,
        "sw_version": device.version,
    }
    _attr_state = None
    _attr_unit_of_measurement = None
    _attr_icon = "mdi:thermometer"

    def __init__(self, device, entry_id):
        """Initialize the sensor entity."""
        self._device = device
        self._entry_id = entry_id
        self._status_updated_signal = SIGNAL_STATE_UPDATED.format(f"{entry_id}_temperature")

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self._status_updated_signal, self.async_write_ha_state
            )
        )

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._device.temperature
    
    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._device.temperature_unit
    
    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return DEVICE_CLASS_TEMPERATURE
    
    @property
    def device_info(self):
        """Return device information."""
        return self._attr_device_info
    
    @property
    def icon(self):
        """Return the icon to display."""
        return self._attr_icon
    
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

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self._status_updated_signal, self.async_write_ha_state
            )
        )