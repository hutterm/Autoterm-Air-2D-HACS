
"""Select platform for Autoterm integration."""
import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, MANUFACTURER, MODEL, SENSOR_OPTIONS, MODE_OPTIONS
from .device import SIGNAL_STATE_UPDATED, AutotermDevice

_LOGGER = logging.getLogger(__name__)
ATTR_SELECTED_ENTITY_ID = "selected_entity_id"

SELECT_TYPES = {
    "sensor": ("Temperature Sensor", SENSOR_OPTIONS),
    "mode": ("Operating Mode", MODE_OPTIONS),
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Autoterm select platform."""
    device: AutotermDevice = hass.data[DOMAIN][entry.entry_id]
    entities = [AutotermSelect(device, entry.entry_id, key) for key in SELECT_TYPES]
    entities.append(ExternalTemperatureSensorSelect(hass, device, entry.entry_id))
    async_add_entities(entities)

class ExternalTemperatureSensorSelect(SelectEntity, RestoreEntity):
    """Representation of an external temperature sensor select entity."""

    _attr_has_entity_name = True

    def __init__(self, hass, device: AutotermDevice, entry_id: str):
        """Initialize the select entity."""
        self._device = device
        self._entry_id = entry_id
        self._attr_unique_id = f"{entry_id}_external_temperature_sensor"
        self._attr_translation_key = "external_temperature_sensor"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
        }
        self._hass = hass
        self._options = self.get_all_temperature_sensors(hass)
        self._status_updated_signal = SIGNAL_STATE_UPDATED.format(f"{entry_id}_external_temperature_sensor")

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to Home Assistant."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self._status_updated_signal, self.async_write_ha_state
            )
        )
        await self._restore_selected_sensor()
    
    def get_all_temperature_sensors(self, hass: HomeAssistant) -> dict:
        """Return all available temperature sensors with a None option."""
        entities = hass.states.async_all("sensor")
        sensors = {"none": "None"}  # Add "None" as the first option
        for entity in entities:
            if entity.attributes.get("device_class") == "temperature":
                sensors[entity.entity_id] = entity.name
        return sensors
    
    @property
    def options(self) -> list[str]:
        """Return a set of available options."""
        # Refresh available sensors each time options are requested
        self._options = self.get_all_temperature_sensors(self._hass)
        return list(self._options.values())

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        option = self._device.get_external_temperature_sensor()
        if option is None:
            return self._options.get("none")
        if option and option in self._options:
            return self._options.get(option)
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        for key, value in self._options.items():
            if value == option:
                if key == "none":
                    await self._device.set_external_temperature_sensor(None)
                else:
                    await self._device.set_external_temperature_sensor(key)
                    await self._submit_external_temperature_from_sensor(key)
                self.async_write_ha_state()
                return

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return the selected temperature sensor entity id for state restore."""
        selected_entity_id = self._device.get_external_temperature_sensor() or "none"
        return {ATTR_SELECTED_ENTITY_ID: selected_entity_id}

    async def _restore_selected_sensor(self) -> None:
        """Restore selected external sensor across Home Assistant restarts."""
        last_state = await self.async_get_last_state()
        if not last_state:
            return

        restored_entity_id = last_state.attributes.get(ATTR_SELECTED_ENTITY_ID)
        if restored_entity_id is None:
            if last_state.state == self._options.get("none"):
                restored_entity_id = "none"
            else:
                for key, value in self._options.items():
                    if value == last_state.state:
                        restored_entity_id = key
                        break

        if restored_entity_id == "none":
            await self._device.set_external_temperature_sensor(None)
            return

        if isinstance(restored_entity_id, str):
            await self._device.set_external_temperature_sensor(restored_entity_id)
            await self._submit_external_temperature_from_sensor(restored_entity_id)

    async def _submit_external_temperature_from_sensor(self, sensor_entity_id: str) -> None:
        """Submit current selected sensor temperature to the heater."""
        temp_state = self._hass.states.get(sensor_entity_id)
        if not temp_state:
            _LOGGER.debug("Temperature entity %s not found", sensor_entity_id)
            return
        if temp_state.state in ("unknown", "unavailable"):
            _LOGGER.debug(
                "Temperature entity %s has non-numeric state %s",
                sensor_entity_id,
                temp_state.state,
            )
            return
        try:
            temp_value = float(temp_state.state)
        except (ValueError, TypeError):
            _LOGGER.debug(
                "Temperature entity %s has invalid numeric value %s",
                sensor_entity_id,
                temp_state.state,
            )
            return
        await self._device.submit_external_temperature(temp_value)

class AutotermSelect(SelectEntity):
    """Representation of an Autoterm select entity."""

    _attr_has_entity_name = True

    def __init__(self, device: AutotermDevice, entry_id: str, key: str):
        """Initialize the select entity."""
        self._device = device
        self._entry_id = entry_id
        self._key = key
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_translation_key = key
        _, self._options = SELECT_TYPES[key]
        self._attr_options = list(self._options.values())
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
    def current_option(self) -> str | None:
        """Return the current selected option."""
        key_value = self._device.get_entity_state(self._key)
        _LOGGER.info(f"Current Option {self._key}: {key_value}")
        return self._options.get(key_value)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        
        for key, value in self._options.items():
            if value == option:
                if self._key == "sensor":
                    await self._device.set_sensor(key)
                elif self._key == "mode":
                    await self._device.set_mode(key)
                self.async_write_ha_state()
                return
