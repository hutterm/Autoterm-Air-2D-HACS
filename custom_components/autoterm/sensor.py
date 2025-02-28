"""Sensor platform for Autoterm integration."""
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfTemperature, UnitOfElectricPotential
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODEL
from .device import SIGNAL_STATE_UPDATED, AutotermDevice

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "temperature_intake": ("Intake Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
    "temperature_sensor": ("External Sensor Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
    "temperature_heat_exchanger": ("Heat Exchanger Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
    "temperature_panel": ("Control Panel Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
    "voltage": ("Voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    "fan_rpm_actual": ("Fan RPM", None, None, SensorStateClass.MEASUREMENT),
    "frequency_fuel_pump": ("Fuel Pump Frequency", "Hz", SensorDeviceClass.FREQUENCY , SensorStateClass.MEASUREMENT),
    "status": ("Status", None, None, None),
    "status_code": ("Status Code", None, None, None),
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Autoterm sensor platform."""
    device: AutotermDevice = hass.data[DOMAIN][entry.entry_id]
    entities = [AutotermSensor(device, entry.entry_id, key) for key in SENSOR_TYPES]
    async_add_entities(entities)

class AutotermSensor(SensorEntity):
    """Representation of an Autoterm sensor entity."""

    def __init__(self, device: AutotermDevice, entry_id: str, key: str):
        """Initialize the sensor entity."""
        self._device = device
        self._entry_id = entry_id
        self._key = key
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_name, self._attr_native_unit_of_measurement, self._attr_device_class,self._attr_state_class  = SENSOR_TYPES[key]
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
        """Return the current state of the sensor."""
        return self._device.get_entity_state(self._key)

