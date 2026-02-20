# AGENTS.md

Guidelines for AI coding agents working in this repository.

## Project Overview

This is a **Home Assistant custom component** (HACS integration) for the Autoterm Air 2D diesel heater. It communicates via serial/USB connection using a custom binary protocol.

## Build / Lint / Test Commands

### Validation
```bash
# Run Home Assistant's hassfest validation (used in CI)
# This validates manifest.json, code structure, and HA integration requirements
# Requires home-assistant/actions/hassfest GitHub Action
```

### Running Tests
```bash
# No automated tests exist in this repository currently
# Manual testing: Install via HACS and configure through HA UI
```

### Development Setup
```bash
# Clone or symlink the custom_components/autoterm folder to:
# <home-assistant-config>/custom_components/autoterm/

# Restart Home Assistant to load changes
# Configure via Settings > Devices & Services > Add Integration > Autoterm Heater
```

## Code Style Guidelines

### Import Order
```python
# 1. Standard library
import asyncio
import logging
from typing import Any

# 2. Third-party packages
import serial
import voluptuous as vol

# 3. Home Assistant imports
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

# 4. Local imports
from .const import DOMAIN, CONF_SERIAL_PORT
from .device import AutotermDevice
```

### Module Structure
- Module docstring at the top: `"""Description of the module."""`
- Logger setup: `_LOGGER = logging.getLogger(__name__)`
- Constants in ALL_CAPS at module level
- Classes before functions when both exist

### Naming Conventions
- **Files**: lowercase with underscores (`climate.py`, `config_flow.py`)
- **Classes**: PascalCase (`AutotermDevice`, `AutotermSensor`)
- **Functions/Methods**: snake_case (`async_setup_entry`, `set_temperature_target`)
- **Constants**: UPPER_SNAKE_CASE (`DOMAIN`, `CONF_SERIAL_PORT`, `MESSAGE_IDS`)
- **Private attributes**: leading underscore (`_device`, `_entry_id`, `_running`)
- **Signal names**: UPPER_SNAKE_CASE with format placeholder (`SIGNAL_STATE_UPDATED = "autoterm_state_updated_{}"`)

### Type Hints
- Use type hints for all function parameters and return types
- Use `Any` from typing when needed
- Union types: `str | None` (modern Python 3.10+ style)

```python
async def set_control(self, key: str) -> None:
def get_entity_state(self, entity_key: str) -> Any:
def get_external_temperature_sensor(self) -> str | None:
```

### Logging
```python
# Module-level logger
_LOGGER = logging.getLogger(__name__)

# Log levels
_LOGGER.debug("Detailed message: %s", value)
_LOGGER.info("Important event happened")
_LOGGER.error("Error occurred: %s", ex)
```

### Async Patterns
- All setup functions must be async: `async def async_setup_entry(...)`
- Use `await` for coroutines
- Use `asyncio.sleep()` for delays (not `time.sleep()`)
- Lock usage for shared resources: `async with self._writer_lock:`

### Error Handling
```python
try:
    await device.connect()
except Exception as ex:
    _LOGGER.error(f"Failed to connect to Autoterm device: {ex}")
    return False
```

### Home Assistant Entity Patterns

#### Entity Class Attributes
Use class-level `_attr_` attributes for entity configuration:
```python
class AutotermClimate(ClimateEntity):
    _attr_has_entity_name = True
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.FAN_ONLY]
```

#### Device Info
```python
self._attr_device_info = {
    "identifiers": {(DOMAIN, entry_id)},
    "name": "Autoterm Air 2D",
    "manufacturer": MANUFACTURER,
    "model": MODEL,
}
```

#### State Update Pattern
Use the dispatcher pattern for state updates:
```python
# In device.py - signal constant
SIGNAL_STATE_UPDATED = "autoterm_state_updated_{}"

# In device.py - notify
def _notify_state_update(self, entity_key: str) -> None:
    signal = SIGNAL_STATE_UPDATED.format(f"{self.entry_id}_{entity_key}")
    async_dispatcher_send(self.hass, signal)

# In entity - subscribe
async def async_added_to_hass(self) -> None:
    self.async_on_remove(
        async_dispatcher_connect(
            self.hass, 
            self._status_updated_signal, 
            self.async_write_ha_state
        )
    )
```

#### Platform Setup
```python
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Autoterm [platform] platform."""
    device: AutotermDevice = hass.data[DOMAIN][entry.entry_id]
    entities = [AutotermEntity(device, entry.entry_id, key) for key in ENTITY_TYPES]
    async_add_entities(entities)
```

### Constants File Pattern (`const.py`)
```python
# Domain and metadata
DOMAIN = "autoterm"
MANUFACTURER = "Autoterm"
MODEL = "Air 2D"

# Configuration keys
CONF_SERIAL_PORT = "serial_port"

# Lookup dictionaries
MESSAGE_IDS = {
    0x01: "heat",
    0x02: "settings",
}

# Reverse lookup
MESSAGE_IDS_REV = {v: k for k, v in MESSAGE_IDS.items()}
```

## File Structure

```
custom_components/autoterm/
├── __init__.py        # Integration setup, async_setup_entry, async_unload_entry
├── climate.py         # ClimateEntity for HVAC control
├── config_flow.py     # ConfigFlow for UI configuration
├── const.py           # Domain constants, message IDs, options
├── device.py          # AutotermDevice class with serial communication
├── manifest.json      # HA integration manifest (domain, version, requirements)
├── number.py          # NumberEntity for temperature/power settings
├── select.py          # SelectEntity for mode/sensor selection
├── sensor.py          # SensorEntity for read-only values
└── translations/      # Localization JSON files (en.json, de.json)
```

## Important Notes

- This integration uses **pyserial** for serial communication
- Binary protocol uses 0xAA as start byte with CRC-16 checksum
- State updates are pushed (not polled) from the device
- The device stores settings that must be read before modification
- All serial operations should use `run_in_executor` to avoid blocking
