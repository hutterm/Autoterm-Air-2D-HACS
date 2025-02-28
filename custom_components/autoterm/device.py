"""Main device implementation for Autoterm heater."""
import asyncio
import logging
import struct
from typing import Any, Callable, Dict, List, Optional, Tuple

import serial
import serial.tools.list_ports

from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    CONTROL_OPTIONS,
    DIAG_MESSAGE_IDS,
    ERROR_PROCESS_SETTINGS_MESSAGE,
    ERROR_PROCESS_STATUS_MESSAGE,
    ERROR_PROCESS_TEMPERATURE_MESSAGE,
    LEVEL_OPTIONS,
    MESSAGE_IDS,
    MESSAGE_IDS_REV,
    MESSAGE_TYPES,
    MODE_OPTIONS,
    SENSOR_OPTIONS,
    STATUS_OPTIONS,
    TEMP_MAX,
    TEMP_MIN,
)

_LOGGER = logging.getLogger(__name__)

SIGNAL_STATE_UPDATED = "autoterm_state_updated_{}"


class AutotermDevice:
    """Representation of an Autoterm heater device."""

    def __init__(self, port: str, loop: asyncio.AbstractEventLoop, entry_id: str):
        """Initialize the Autoterm device."""
        self.port = port
        self.loop = loop
        self.entry_id = entry_id
        self.serial = None
        self.settings = None
        self.version = None
        self._entities = {}
        self._writer_lock = asyncio.Lock()
        self._running = False
        self._read_task = None
        
        # State data
        self.status_data = {}
        self.settings_data = {}
        self.temperature_data = {}

    async def connect(self) -> bool:
        """Connect to the device."""
        try:
            self.serial = await self.loop.run_in_executor(
                None, 
                lambda: serial.Serial(
                    self.port, 
                    baudrate=9600, 
                    timeout=1
                )
            )
            
            # Start serial read task
            self._running = True
            self._read_task = self.loop.create_task(self._read_serial())
            
            # Initial device information request
            await self.send_message('version')
            await asyncio.sleep(0.5)
            await self.send_message('status')
            await asyncio.sleep(0.5)
            await self.send_message('settings')
            
            return True
        except Exception as ex:
            _LOGGER.error(f"Failed to connect to Autoterm device: {ex}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from the device."""
        self._running = False
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
        
        if self.serial:
            await self.loop.run_in_executor(None, self.serial.close)
            self.serial = None

    async def _read_serial(self) -> None:
        """Task to read data from the serial port."""
        while self._running:
            try:
                # Check if data is available
                if self.serial.in_waiting:
                    # Read byte by byte until we find the start marker (0xAA)
                    start_byte = await self.loop.run_in_executor(None, self.serial.read, 1)
                    if start_byte and start_byte[0] == 0xAA:
                        # Read the type byte
                        type_byte = await self.loop.run_in_executor(None, self.serial.read, 1)
                        if type_byte:
                            # Read length byte
                            length_byte = await self.loop.run_in_executor(None, self.serial.read, 1)
                            if length_byte:
                                payload_length = length_byte[0]
                                # Read the rest of the message (padding byte + id + payload + 2 checksum bytes)
                                rest_of_message = await self.loop.run_in_executor(
                                    None, self.serial.read, 2 + payload_length + 2
                                )
                                if len(rest_of_message) == 2 + payload_length + 2:
                                    # Construct the full message
                                    full_message = start_byte + type_byte + length_byte + rest_of_message
                                    # Process the message
                                    await self.process_message(full_message)
                else:
                    # No data available, sleep a bit
                    await asyncio.sleep(0.01)
            except Exception as ex:
                _LOGGER.error(f"Error reading from serial port: {ex}")
                await asyncio.sleep(1)  # Sleep before retrying

    @callback
    def register_entity(self, entity_key: str, entity) -> None:
        """Register an entity with the device."""
        self._entities[entity_key] = entity

    @callback
    def get_entity_state(self, entity_key: str) -> Any:
        """Get the current state for an entity."""
        # Temperature entities
        if entity_key == "temperature_intake" and "boardTemp" in self.status_data:
            value = self.status_data["boardTemp"]
            return value > 127 and value - 255 or value
        elif entity_key == "temperature_sensor" and "externalTemp" in self.status_data:
            return self.status_data["externalTemp"]
        elif entity_key == "temperature_heat_exchanger" and "temperatureHeatExchanger" in self.status_data:
            return self.status_data["temperatureHeatExchanger"]
        elif entity_key == "temperature_panel" and "value" in self.temperature_data:
            return self.temperature_data["value"]
        elif entity_key == "temperature_target" and "targetTemperature" in self.settings_data:
            return self.settings_data["targetTemperature"]
            
        # Status entities
        elif entity_key == "status_code" and "statusCode" in self.status_data:
            return self.status_data["statusCode"]
        elif entity_key == "status" and "status" in self.status_data:
            return self.status_data["status"]
            
        # Diagnostic entities
        elif entity_key == "voltage" and "voltage" in self.status_data:
            return self.status_data["voltage"]
        elif entity_key == "fan_rpm_specified" and "fanRpmSpecified" in self.status_data:
            return self.status_data["fanRpmSpecified"]
        elif entity_key == "fan_rpm_actual" and "fanRpmActual" in self.status_data:
            return self.status_data["fanRpmActual"]
        elif entity_key == "frequency_fuel_pump" and "frequencyFuelPump" in self.status_data:
            return self.status_data["frequencyFuelPump"]
        elif entity_key == "blackbox_version" and self.version:
            return self.version
            
        # Control entities
        elif entity_key == "control" and "control" in self.status_data:
            control_key = self.status_data["control"]
            return CONTROL_OPTIONS.get(control_key, "Unknown")
        elif entity_key == "level" and "level" in self.settings_data:
            level_key = self.settings_data["level"]
            return LEVEL_OPTIONS.get(level_key, "Unknown")
        elif entity_key == "power" and "level" in self.settings_data:
            return self.settings_data["level"] + 1
        elif entity_key == "work_time" and "workTime" in self.settings_data:
            return self.settings_data["workTime"]
        elif entity_key == "sensor" and "sensor" in self.settings_data:
            sensor_key = self.settings_data["sensor"]
            return SENSOR_OPTIONS.get(sensor_key, "Unknown")
        elif entity_key == "mode" and "mode" in self.settings_data:
            mode_key = self.settings_data["mode"]
            return MODE_OPTIONS.get(mode_key, "Unknown")
            
        return None

    async def send_message(self, key: str, payload: bytes = b"") -> None:
        """Send a message to the device."""
        if not self.serial:
            raise Exception("Not connected to device")
            
        async with self._writer_lock:
            try:
                message_id = MESSAGE_IDS_REV.get(key)
                if message_id is None:
                    raise ValueError(f"Unknown message key: {key}")
                
                # Construct header
                header = bytes([0xAA, 0x03, len(payload), 0x00, message_id])
                
                # Calculate checksum
                checksum = self._calc_checksum(header + payload)
                
                # Construct full message
                message = header + payload + checksum
                
                # Send message
                await self.loop.run_in_executor(None, self.serial.write, message)
                
                # Wait for a moment to ensure the message is sent
                await asyncio.sleep(0.1)
                
                return True
            except Exception as ex:
                _LOGGER.error(f"Error sending message: {ex}")
                raise

    def _calc_checksum(self, data: bytes) -> bytes:
        """Calculate the checksum for a message."""
        crc = 0xFFFF
        
        for byte in data:
            crc = crc ^ byte
            
            for _ in range(8):
                odd = crc & 0x0001
                crc >>= 1
                
                if odd:
                    crc ^= 0xA001
                    
        return bytes([(crc >> 8) & 0xFF, crc & 0xFF])

    async def process_message(self, buffer: bytes) -> None:
        """Process a message from the device."""
        if len(buffer) < 5:
            _LOGGER.error("Buffer too short")
            return
            
        try:
            type_value = buffer[1]
            type_str = MESSAGE_TYPES.get(type_value, f"Unknown ({type_value})")
            length = buffer[2]
            payload = buffer[5:5+length]
            
            if type_str in ["request", "response"]:
                id_value = buffer[4]
                id_str = MESSAGE_IDS.get(id_value, f"Unknown ({id_value})")
            elif type_str == "diag":
                id_value = buffer[4]
                id_str = DIAG_MESSAGE_IDS.get(id_value, f"Unknown ({id_value})")
            else:
                id_str = f"Unknown ({buffer[4]})"
                
            if type_str == "response":
                if id_str == "version":
                    await self._process_version_message(payload)
                elif id_str == "status":
                    await self._process_status_message(payload)
                elif id_str == "settings":
                    await self._process_settings_message(payload)
                elif id_str == "temperature":
                    await self._process_temperature_message(payload)
        except Exception as ex:
            _LOGGER.error(f"Error processing message: {ex}")

    async def _process_version_message(self, buffer: bytes) -> None:
        """Process a version message."""
        if len(buffer) < 5:
            return
            
        version_parts = [str(int(b)) for b in buffer[:4]]
        self.version = ".".join(version_parts)
        
        self._notify_state_update("blackbox_version")
        _LOGGER.info(f"Connected to Autoterm heater with version: {self.version}")

    async def _process_status_message(self, buffer: bytes) -> None:
        """Process a status message."""
        try:
            if len(buffer) < 15:
                raise ValueError("Buffer too short")
                
            self.status_data = {
                "statusCode": f"{buffer[0]}.{buffer[1]}",
                "boardTemp": buffer[3],
                "externalTemp": struct.unpack("b", bytes([buffer[4]]))[0],  # Signed byte
                "voltage": buffer[6] / 10,
                "temperatureHeatExchanger": buffer[8] - 15,
                "fanRpmSpecified": buffer[11] * 60,
                "fanRpmActual": buffer[12] * 60,
                "frequencyFuelPump": buffer[14] / 100,
            }
            
            # Determine control state based on status code
            if self.status_data["statusCode"] in ["0.1", "4.0"]:
                self.status_data["control"] = "off"
            elif self.status_data["statusCode"] == "3.35":
                self.status_data["control"] = "fan_only"
            else:
                self.status_data["control"] = "heat"
                
            # Add status text
            self.status_data["status"] = STATUS_OPTIONS.get(
                self.status_data["statusCode"], "unbekannt"
            )
            
            # Notify entities of state changes
            self._notify_state_update("temperature_intake")
            self._notify_state_update("temperature_sensor")
            self._notify_state_update("temperature_heat_exchanger")
            self._notify_state_update("status_code")
            self._notify_state_update("status")
            self._notify_state_update("voltage")
            self._notify_state_update("fan_rpm_specified")
            self._notify_state_update("fan_rpm_actual")
            self._notify_state_update("frequency_fuel_pump")
            self._notify_state_update("control")
            
        except Exception as ex:
            _LOGGER.error(f"{ERROR_PROCESS_STATUS_MESSAGE}{ex}")

    async def _process_settings_message(self, buffer: bytes) -> None:
        """Process a settings message."""
        try:
            if len(buffer) < 6:
                raise ValueError("Buffer too short")
                
            self.settings = buffer
            
            self.settings_data = {
                "workTime": (buffer[0] << 8 | buffer[1]) / 60,
                "sensor": buffer[2],
                "targetTemperature": buffer[3],
                "mode": buffer[4],
                "level": buffer[5],
            }
            
            # Notify entities of state changes
            self._notify_state_update("work_time")
            self._notify_state_update("sensor")
            self._notify_state_update("temperature_target")
            self._notify_state_update("mode")
            self._notify_state_update("level")
            self._notify_state_update("power")
            
        except Exception as ex:
            _LOGGER.error(f"{ERROR_PROCESS_SETTINGS_MESSAGE}{ex}")

    async def _process_temperature_message(self, buffer: bytes) -> None:
        """Process a temperature message."""
        try:
            if len(buffer) < 1:
                raise ValueError("Buffer too short")
                
            self.temperature_data = {
                "value": buffer[0]
            }
            
            # Notify entities of state changes
            self._notify_state_update("temperature_panel")
            
        except Exception as ex:
            _LOGGER.error(f"{ERROR_PROCESS_TEMPERATURE_MESSAGE}{ex}")

    def _notify_state_update(self, entity_key: str) -> None:
        """Notify an entity of a state update."""
        signal = SIGNAL_STATE_UPDATED.format(f"{self.entry_id}_{entity_key}")
        async_dispatcher_send(self.loop, signal)

    # ---- Control methods ----
    
    async def set_temperature_current(self, value: int) -> None:
        """Set the current temperature."""
        await self.send_message("temperature", bytes([int(value)]))

    async def set_work_time(self, value: float) -> None:
        """Set the work time in hours."""
        if value > 0:
            value_minutes = int(value * 60)
            self.settings = bytearray(self.settings)
            self.settings[0] = value_minutes >> 8
            self.settings[1] = value_minutes & 0xFF
        else:
            self.settings = bytearray(self.settings)
            self.settings[0] = 0xFF
            self.settings[1] = 0xFF
            
        await self.send_message("settings", bytes(self.settings))

    async def set_sensor(self, value: str) -> None:
        """Set the temperature sensor."""
        # Find the key for the value
        for key, val in SENSOR_OPTIONS.items():
            if val == value:
                self.settings = bytearray(self.settings)
                self.settings[2] = key
                await self.send_message("settings", bytes(self.settings))
                return

    async def set_temperature_target(self, value: int) -> None:
        """Set the target temperature."""
        self.settings = bytearray(self.settings)
        self.settings[3] = int(value)
        await self.send_message("settings", bytes(self.settings))

    async def set_mode(self, value: str) -> None:
        """Set the operation mode."""
        # Find the key for the value
        for key, val in MODE_OPTIONS.items():
            if val == value:
                self.settings = bytearray(self.settings)
                self.settings[4] = key
                await self.send_message("settings", bytes(self.settings))
                return

    async def set_power(self, value: int) -> None:
        """Set the power level 1-10."""
        await self.set_level(value - 1)

    async def set_level(self, value: int) -> None:
        """Set the level 0-9."""
        if 0 <= value <= 9:
            self.settings = bytearray(self.settings)
            self.settings[5] = value
            await self.send_message("settings", bytes(self.settings))

    async def set_control(self, value: str) -> None:
        """Set the control mode (off, heat, fan_only)."""
        # Find the key for the value
        for key, val in CONTROL_OPTIONS.items():
            if val == value:
                if key == "off":
                    await self.send_message("off")
                elif key == "fan_only":
                    await self.send_message("fan_only", bytes([0x00, 0x00, self.settings[5], 0xFF]))
                elif key == "heat":
                    await self.send_message("heat", bytes(self.settings))
                return
