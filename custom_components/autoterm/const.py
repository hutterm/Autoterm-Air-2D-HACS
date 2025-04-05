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
    #0x00: "unbekannt",
    0x01: "Heizgerät",
    0x02: "Bedienpanel", # this is using temperature via set temp
    #0x03: "extern",
    0x04: "Manuell" # this is using set power
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
    0x00: "Temperatur halten", 
        # leistung wird verringert ohne abschalten
    0x01: "Wärme + Lüftung", 
        # wie Thermostat, aber dauerhaft mit Lüfter
        # heizt bis +1°C, danach lüftet bis -5°C
    0x02: "Stufenreglung", 
        # Leistungsmodus
        # läuft konstant auf eingestellter Stufe
    0x03: "Thermostat" 
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
    "0.1": "Standby",
    "1.0": "Flammensensor kühlen",
    "1.1": "Belüftung",
    "2.0": "Glühkerze aufwärmen",
    "2.1": "Zündvorbereitung",
    "2.2": "Zündung",
    "2.3": "Zündung 2",
    "2.4": "Brennkammer erhitzen",
    "3.0": "Heizvorgang",
    "3.35": "Nur Ventilator",
    "3.4": "Abkühlung",
    "3.5": "Temperaturüberwachung",
    "4.0": "Abschaltung"
}

# Error messages
ERROR_PROCESS_STATUS_MESSAGE = "Cannot process status message: "
ERROR_PROCESS_SETTINGS_MESSAGE = "Cannot process settings message: "
ERROR_PROCESS_TEMPERATURE_MESSAGE = "Cannot process temperature message: "
