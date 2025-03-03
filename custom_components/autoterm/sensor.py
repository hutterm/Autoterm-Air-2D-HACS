"""Sensor platform for Autoterm integration."""
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfTemperature, UnitOfElectricPotential
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
# from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .device import SIGNAL_STATE_UPDATED, AutotermDevice

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "status_code": ("Status Code", None, None, None),
    "status": ("Status", None, None, None),
    "board_temp": ("Intake Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
    #"external_temp": ("External Sensor Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
    "controller_temp": ("Controller Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
    "voltage": ("Voltage", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    #"temperature_heat_exchanger": ("Heat Exchanger Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
    "flame_temperature": ("Flame Temperature", UnitOfTemperature.KELVIN, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
    #"temperature_panel": ("Control Panel Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
    "fan_rpm_specified": ("Fan RPM Specified", None, None, SensorStateClass.MEASUREMENT),
    "fan_rpm_actual": ("Fan RPM", None, None, SensorStateClass.MEASUREMENT),
    "frequency_fuel_pump": ("Fuel Pump Frequency", "Hz", SensorDeviceClass.FREQUENCY , SensorStateClass.MEASUREMENT),
    #"work_time": ("Work Time", "h", SensorDeviceClass.DURATION, SensorStateClass.MEASUREMENT),
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Autoterm sensor platform."""
    device: AutotermDevice = hass.data[DOMAIN][entry.entry_id]
    entities = [AutotermSensor(device, entry.entry_id, key) for key in SENSOR_TYPES]
    # coordinator = device["coordinator"]
    # entities = [AutotermSensor(coordinator, device, entry.entry_id, key) for key in SENSOR_TYPES]
    async_add_entities(entities)

class AutotermSensor(SensorEntity):
# class AutotermSensor(CoordinatorEntity):
    """Representation of an Autoterm sensor entity."""

    def __init__(self, device: AutotermDevice, entry_id: str, key: str):
    # def __init__(self, coordinator, device: AutotermDevice, entry_id: str, key: str, name: str=None):
        """Initialize the sensor entity."""
        # super().__init__(coordinator)
        self._device = device
        self._entry_id = entry_id
        self._key = key
        # self._name = name
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
       
    # @property
    # def available(self):
    #     """Return if entity is available."""
    #     # Use both coordinator availability and the presence of data
    #     return self.coordinator.last_update_success and self._get_value() is not None
        

    # def _get_value(self):
    #     """Get value from coordinator data."""
    #     if not self.coordinator.data:
    #         return None
            
    #     # Map entity_key to appropriate data structure
    #     if self._entity_key.startswith("temperature_"):
    #         if self._entity_key == "temperature_intake" and "boardTemp" in self.coordinator.data["status_data"]:
    #             value = self.coordinator.data["status_data"]["boardTemp"]
    #             return value > 127 and value - 255 or value
    #         elif self._entity_key == "temperature_sensor" and "externalTemp" in self.coordinator.data["status_data"]:
    #             return self.coordinator.data["status_data"]["externalTemp"]
    #         # Add other temperature mappings here
            
    #     elif self._entity_key == "status" and "status" in self.coordinator.data["status_data"]:
    #         return self.coordinator.data["status_data"]["status"]
            
    #     # Add other entity mappings
        
    #     return None

    @property
    def native_value(self) -> Any:
        """Return the current state of the sensor."""
        return self._device.get_entity_state(self._key)

