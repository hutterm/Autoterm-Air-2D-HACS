
"""Select platform for Autoterm integration."""
import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODEL, SENSOR_OPTIONS, MODE_OPTIONS
from .device import SIGNAL_STATE_UPDATED, AutotermDevice

_LOGGER = logging.getLogger(__name__)

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
    async_add_entities(entities)

class AutotermSelect(SelectEntity):
    """Representation of an Autoterm select entity."""

    def __init__(self, device: AutotermDevice, entry_id: str, key: str):
        """Initialize the select entity."""
        self._device = device
        self._entry_id = entry_id
        self._key = key
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_name, self._options = SELECT_TYPES[key]
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
