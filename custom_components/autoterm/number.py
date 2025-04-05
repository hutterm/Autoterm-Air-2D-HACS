
"""Number platform for Autoterm integration."""
import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberDeviceClass
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODEL, TEMP_MIN, TEMP_MAX
from .device import SIGNAL_STATE_UPDATED, AutotermDevice

_LOGGER = logging.getLogger(__name__)

NUMBER_TYPES = {
    "temperature_target": ("Target Temperature",NumberDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS, TEMP_MIN, TEMP_MAX,1),
    "power": ("Power Level",NumberDeviceClass.POWER_FACTOR, None, 10, 100,10),
    "work_time": ("Work Time",NumberDeviceClass.DURATION, UnitOfTime.MINUTES, -5, 720,5),
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Autoterm number platform."""
    device: AutotermDevice = hass.data[DOMAIN][entry.entry_id]
    entities = [AutotermNumber(device, entry.entry_id, key) for key in NUMBER_TYPES]
    async_add_entities(entities)

class AutotermNumber(NumberEntity):
    """Representation of an Autoterm number entity."""

    def __init__(self, device: AutotermDevice, entry_id: str, key: str):
        """Initialize the number entity."""
        self._device = device
        self._entry_id = entry_id
        self._key = key
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_name,self._attr_device_class, self._attr_native_unit_of_measurement, self._attr_native_min_value, self._attr_native_max_value, self._attr_native_step = NUMBER_TYPES[key]
        self._attr_device_class = NumberDeviceClass.TEMPERATURE if key == "temperature_target" else None
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "Autoterm Air 2D",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "sw_version": device.version,
        }
        self._status_updated_signal = SIGNAL_STATE_UPDATED.format(f"{entry_id}_{key}")

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to Home Assistant."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self._status_updated_signal, self.async_write_ha_state
            )
        )

    @property
    def native_value(self) -> Any:
        """Return the current value."""
        return self._device.get_entity_state(self._key)

    async def async_set_native_value(self, value: float) -> None:
        """Set a new value."""
        if self._key == "temperature_target":
            await self._device.set_temperature_target(int(value))
        elif self._key == "power":
            await self._device.set_power(int(value))
        elif self._key == "work_time":
            await self._device.set_work_time(int(value))
        self.async_write_ha_state()

