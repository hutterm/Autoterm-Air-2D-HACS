# Autoterm Heater Integration

This custom integration allows Home Assistant to communicate with an **Autoterm Air 2D Heater** via serial port.

## Features:
- Control heater power (on/off)
- Set target temperature
- Monitor current temperature
- Retrieve heater status

## Installation
1. **Install via HACS**:
   - Add this repository to HACS as a custom repository.
   - Search for `Autoterm Heater Integration` and install it.
2. **Manual Installation**:
   - Copy the `autoterm` folder into `custom_components/`.

## Configuration
1. **Add the following to your `configuration.yaml`:**
   ```yaml
   autoterm:
     port: "/dev/ttyUSB0"
   ```
2. Restart Home Assistant.

## Support
For issues, please open a ticket on [GitHub Issues](https://github.com/your-username/homeassistant-autoterm/issues).
