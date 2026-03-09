# Copilot instructions for this repository

## Build, test, and lint commands

- Validation (CI): `.github/workflows/hassfest.yaml` runs Home Assistant hassfest via `home-assistant/actions/hassfest@master`.
- There are no repository-local lint or test commands configured (`pyproject.toml`, `pytest.ini`, `tox.ini`, `setup.cfg`, and `Makefile` are absent).
- Automated tests: none currently.
- Single test: not applicable (no test suite). Validate changes by loading `custom_components/autoterm` in a Home Assistant instance and checking integration setup and entities.

## High-level architecture

- Bootstrap and lifecycle (`custom_components/autoterm/__init__.py`):
  - `async_setup_entry` constructs `AutotermDevice` from the config-entry serial port and calls `connect()`.
  - The device object is stored directly at `hass.data[DOMAIN][entry.entry_id]` (no coordinator wrapper).
  - Platforms are forwarded to climate, sensor, select, and number.
  - Two periodic tasks are registered:
    - Push selected Home Assistant sensor temperature to heater (`set_temperature_current`) every 60 seconds.
    - Poll heater `status` and `settings` every 5 seconds.
  - `async_unload_entry` unloads platforms, removes the device from `hass.data`, and disconnects serial.
- Serial/protocol core (`custom_components/autoterm/device.py` and `const.py`):
  - Uses pyserial at 9600 baud; blocking serial operations are offloaded with `loop.run_in_executor(...)`.
  - Binary frame format: start `0xAA`, type, payload length, padding byte, message id, payload, CRC-16 checksum.
  - Incoming `status`, `settings`, and `temperature` responses are parsed into `status_data`, `settings_data`, and `temperature_data`.
  - Outbound control APIs (`set_control`, `set_mode`, `set_sensor`, `set_temperature_target`, `set_power`) mutate current settings bytes and send protocol messages.
- Entity layer (`climate.py`, `sensor.py`, `number.py`, `select.py`):
  - Entities read values through `AutotermDevice.get_entity_state(...)`.
  - State updates are event-driven via Home Assistant dispatcher signals.
  - `ExternalTemperatureSensorSelect` enumerates Home Assistant temperature sensors and stores the chosen entity id for periodic push updates.
  - Climate maps heater control/status codes into Home Assistant HVAC modes/actions.
- Config flow (`config_flow.py`):
  - Serial ports are discovered with `serial.tools.list_ports.comports`.
  - Connection validation opens the selected port using `serial.Serial(..., 9600, timeout=1)` before entry creation/update.

## Key conventions

- Dispatcher signals use `SIGNAL_STATE_UPDATED = "autoterm_state_updated_{}"` and keys formatted as `f"{entry_id}_{entity_key}"`.
- Protocol dictionaries in `const.py` (`MESSAGE_IDS`, `MESSAGE_TYPES`, `STATUS_OPTIONS`, `SENSOR_OPTIONS`, `MODE_OPTIONS`) are the source of truth for message parsing and UI options.
- Settings changes follow the same flow in `device.py`:
  - mutate `self.settings` byte offsets,
  - send `"settings"`,
  - then request `"status"` after a short delay.
- Mode/sensor coupling is intentional:
  - Mode `0x02` (Stufenregelung) forces sensor `0x04` (manual).
  - Sensor `0x04` forces mode `0x02`; non-manual sensors can revert mode from `0x02` to `0x03`.
- `controller_temp` is derived state: if sensor is `1`, use board temperature; otherwise use the last external/current temperature value.
- README-defined external sensor behavior is part of expected behavior:
  - `"none"` must remain a valid external sensor option.
  - Selected external sensors are used to push current temperature to the heater periodically.
