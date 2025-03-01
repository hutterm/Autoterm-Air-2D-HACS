
"""Climate platform for Autoterm integration."""
import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.climate.const import HVACAction
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODEL, TEMP_MIN, TEMP_MAX
from .device import SIGNAL_STATE_UPDATED, AutotermDevice

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Autoterm climate platform."""
    device: AutotermDevice = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AutotermClimate(device, entry.entry_id)])

class AutotermClimate(ClimateEntity):
    """Representation of an Autoterm heater climate entity."""

    _attr_has_entity_name = True
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.FAN_ONLY]
    _attr_min_temp = TEMP_MIN
    _attr_max_temp = TEMP_MAX
    _attr_target_temperature_step = 1

    def __init__(self, device: AutotermDevice, entry_id: str):
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
        """Run when entity is added to Home Assistant."""
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
        """Return the current HVAC mode."""
        control = self._device.get_entity_state("control")
        if control == "Aus":
            return HVACMode.OFF
        elif control == "Nur Ventilator":
            return HVACMode.FAN_ONLY
        return HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction:
        """Return the current HVAC action."""
        status = self._device.get_entity_state("status")
        if status == "Abschaltung":
            return HVACAction.OFF
        elif status in ["Flammensensor kühlen", "Belüftung"]:
            return HVACAction.FAN
        elif status in ["Glühkerze aufwärmen", "Zündung", "Brennkammer erhitzen"]:
            return HVACAction.HEATING
        return HVACAction.IDLE

    @property
    def target_temperature(self) -> int | None:
        """Return the target temperature."""
        return self._device.get_entity_state("temperature_target")

    @property
    def current_temperature(self) -> int | None:
        """Return the current temperature."""
        return self._device.get_entity_state("temperature_sensor")

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set a new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is not None:
            await self._device.set_temperature_target(int(temperature))
            self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set a new HVAC mode."""
        _LOGGER.debug("Setting HVAC mode to %s", hvac_mode)
        if hvac_mode == HVACMode.OFF:
            await self._device.set_control("off")
        elif hvac_mode == HVACMode.FAN_ONLY:
            await self._device.set_control("fan_only")
        elif hvac_mode == HVACMode.HEAT:
            await self._device.set_control("heat")
        self.async_write_ha_state()
