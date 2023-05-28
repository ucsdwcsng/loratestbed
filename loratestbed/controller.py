import serial
from typing import List, Tuple
import logging

print (serial.__version__)

# Class for the controller of the lora testbed. 
class SerialInterface:
    def __init__(self, serial_path: str, baud_rate: int = 115200) -> None:
        # Set up Logger
        self._logger = logging.getLogger(__name__)

        # Set up serial port
        self._logger.info(
            f"Setting up serial port at {serial_path} with baud rate {baud_rate}"
        )
        self._serial_port = serial.Serial(serial_path, baud_rate)
        self._logger.info(f"Connected")

    def _write_bytes(self, data: bytes):
        # get length of data
        data_len = len(data)
        self._logger.debug(f"Writing {data_len} bytes to serial port")
        self._serial_port.write(data)        
        
    def _read_bytes(self, data_len: int, block=True):
        # get length of data
        if(block == False and self._serial_port.in_waiting < data_len):
            return None

        self._logger.debug(f"Reading {data_len} bytes from serial port")
        return self._serial_port.read(data_len)   

    def _write_read_bytes(self, data: bytes):
        self._write_bytes(data)
        return self._read_bytes(len(data))



