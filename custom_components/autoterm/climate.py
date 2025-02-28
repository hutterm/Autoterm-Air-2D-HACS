import logging
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import HVACMode, ClimateEntityFeature
from homeassistant.const import TEMP_CELSIUS
from .autoterm import AutotermHeater

_LOGGER = logging.getLogger(__name__)

SUPPORTED_HVAC_MODES = [HVACMode.OFF, HVACMode.HEAT]

class AutotermClimate(ClimateEntity):
    def __init__(self, heater: AutotermHeater):
        self._heater = heater
        self._attr_name = "Autoterm Heater"
        self._attr_hvac_modes = SUPPORTED_HVAC_MODES
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
        self._attr_temperature_unit = TEMP_CELSIUS
        self._attr_target_temperature = heater.target_temperature
        self._attr_current_temperature = None
        self._attr_hvac_mode = HVACMode.OFF

    def update(self):
        status = self._heater.request_status()
        if status:
            self._attr_current_temperature = self._heater.current_temperature

    def set_temperature(self, **kwargs):
        temp = kwargs.get("temperature")
        if temp is not None:
            self._heater.set_temperature(temp)
            self._attr_target_temperature = temp

    def set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVACMode.HEAT:
            self._heater.turn_on()
        elif hvac_mode == HVACMode.OFF:
            self._heater.turn_off()
        self._attr_hvac_mode = hvac_mode
