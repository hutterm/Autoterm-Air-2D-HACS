import serial
import time
import logging
import struct

_LOGGER = logging.getLogger(__name__)

MESSAGE_IDS = {
    0x01: "heat",
    0x02: "settings",
    0x03: "off",
    0x06: "version",
    0x0F: "status",
    0x11: "temperature",
}

class AutotermHeater:
    def __init__(self, port: str, baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.target_temperature = 20
        self.current_temperature = None

    def connect(self):
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=2)
            _LOGGER.info("Connected to Autoterm heater on %s", self.port)
        except serial.SerialException as e:
            _LOGGER.error("Failed to connect to Autoterm heater: %s", e)

    def disconnect(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            _LOGGER.info("Disconnected from Autoterm heater")

    def send_command(self, message_id, payload=b"\x00"):
        if message_id not in MESSAGE_IDS:
            _LOGGER.error("Invalid message ID: %s", message_id)
            return None

        header = struct.pack("BBB", 0xAA, 0x03, len(payload))
        message = header + struct.pack("B", message_id) + payload
        checksum = self._calculate_checksum(message)
        full_message = message + checksum

        _LOGGER.debug("Sending: %s", full_message.hex())
        self.serial_conn.write(full_message)
        time.sleep(0.1)
        return self.read_response()

    def read_response(self):
        response = self.serial_conn.read(20)  # Read up to 20 bytes
        if response:
            _LOGGER.debug("Received: %s", response.hex())
            return self._parse_response(response)
        return None

    def _calculate_checksum(self, data):
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return struct.pack("BB", crc & 0xFF, (crc >> 8) & 0xFF)

    def _parse_response(self, response):
        if len(response) < 5:
            _LOGGER.error("Invalid response length")
            return None
        
        message_type = response[1]
        message_id = response[4]
        payload = response[5:-2]

        if message_id in MESSAGE_IDS:
            return {"type": MESSAGE_IDS[message_id], "payload": payload}
        
        _LOGGER.warning("Unknown message ID: %s", message_id)
        return None

    def request_status(self):
        response = self.send_command(0x0F)
        if response:
            self.current_temperature = response.get("payload", [0])[0]
        return response
    
    def request_settings(self):
        return self.send_command(0x02)
    
    def turn_on(self):
        return self.send_command(0x01)
    
    def turn_off(self):
        return self.send_command(0x03)
    
    def set_temperature(self, temperature):
        if 0 <= temperature <= 30:
            self.target_temperature = temperature
            return self.send_command(0x11, struct.pack("B", temperature))
        else:
            _LOGGER.error("Temperature out of range (0-30°C)")
            return None