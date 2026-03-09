"""Constants for the Autoterm Heater integration."""

DOMAIN = "autoterm"
MANUFACTURER = "Autoterm"
MODEL = "Air 2D"

# Config
CONF_SERIAL_PORT = "serial_port"


# Constants for service
SERVICE_UPDATE_TEMPERATURE = "update_external_temperature"
ATTR_TEMPERATURE_ENTITY = "temperature_entity_id"

# Defaults
DEFAULT_NAME = "Autoterm Heater"

# Temp ranges
TEMP_MIN = 0
TEMP_MAX = 30

# Message Types
MESSAGE_TYPES = {
    0x02: "diag",
    0x03: "request",
    0x04: "response"
}

# Message IDs
MESSAGE_IDS = {
    0x01: "heat",
    0x02: "settings",
    0x03: "off",
    0x04: "serialnum",
    0x06: "version",
    0x07: "diag_control",
    0x08: "fan_speed",
    0x0B: "report",
    0x0D: "unlock",
    0x0F: "status",
    0x11: "temperature",
    0x13: "fuel_pump",
    0x1C: "start",
    0x1E: "misc_3",
    0x23: "fan_only"
}

# Reverse lookup for message IDs
MESSAGE_IDS_REV = {v: k for k, v in MESSAGE_IDS.items()}

# Diagnostic message IDs
DIAG_MESSAGE_IDS = {
    0x00: "connect",
    0x01: "heater"
}

# Sensor options
SENSOR_OPTIONS = {
    # 0x00: "unknown",
    0x01: "heater",
    0x02: "control_panel",
    # 0x03: "external",
    0x04: "manual",
}
# kann nicht geändert werden in Stufenregelung/Thermostat

# Level options
LEVEL_OPTIONS = {
    0x00: "10%",
    0x01: "20%",
    0x02: "30%",
    0x03: "40%",
    0x04: "50%",
    0x05: "60%",
    0x06: "70%",
    0x07: "80%",
    0x08: "90%",
    0x09: "100%"
}

# Mode options
MODE_OPTIONS = {
    0x00: "hold_temperature",
        # leistung wird verringert ohne abschalten
    0x01: "heat_ventilation",
        # wie Thermostat, aber dauerhaft mit Lüfter
        # heizt bis +1°C, danach lüftet bis -5°C
    0x02: "step_control",
        # Leistungsmodus
        # läuft konstant auf eingestellter Stufe
    0x03: "thermostat"
        # schaltet ein und aus um die Temperatur zu halten, 
        # Standartwerte: +1°C, -2°C
        # Einstellwerte: 
        # +1°C -> +3°C, -1°C -> -7°C
}



# Control options
CONTROL_OPTIONS = {
    "off": "hvac_mode.off",
    "heat": "hvac_mode.heat",
    "fan_only": "hvac_mode.fan_only"
}

# Reverse lookup for control options
CONTROL_OPTIONS_REV = {v: k for k, v in CONTROL_OPTIONS.items()}

# Status options
STATUS_OPTIONS = {
    "0.1": "standby",
    "1.0": "cooling_flame_sensor",
    "1.1": "ventilation",
    "2.0": "heating_glowplug",
    "2.1": "pre_ignition",
    "2.2": "ignition",
    "2.3": "ignition_2",
    "2.4": "heating_combustion_chamber",
    "2.5": "no_ignition",
    "2.6": "no_diesel_retry",
    "3.0": "heating",
    "3.11": "overheat_protection",
    "3.35": "fan_only",
    "3.4": "cooling_down",
    "3.5": "temperature_monitoring",
    "4.0": "shutting_down"
}

# Error messages
ERROR_PROCESS_STATUS_MESSAGE = "Cannot process status message: "
ERROR_PROCESS_SETTINGS_MESSAGE = "Cannot process settings message: "
ERROR_PROCESS_TEMPERATURE_MESSAGE = "Cannot process temperature message: "
