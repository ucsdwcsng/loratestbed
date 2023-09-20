import time
import serial
from typing import List, Tuple
import loratestbed.utils as utils
import logging
import numpy as np
from enum import Enum


class SerialInterface:
    """Serial Interface for communicating with the LoRa Testbed Controller"""

    def __init__(self, serial_port: str, baud_rate: int = 115200) -> None:
        # Set up Logger
        self._logger = logging.getLogger(__name__)

        # Set up serial port
        self._logger.info(
            f"Setting up serial port at {serial_port} with baud rate {baud_rate}"
        )
        self._serial_port = serial.Serial(serial_port, baud_rate)
        self._logger.info(f"Connected")

    def _flush(self):
        # This function flushes input and output buffers
        self._serial_port.reset_input_buffer()
        self._serial_port.reset_output_buffer()

    def _set_read_timeout(self, timeout: float):
        # This function sets the timeout for read operations
        pass

    def _write_bytes(self, data: bytes):
        # get length of data
        data_len = len(data)
        self._logger.debug(f"Writing {data_len} bytes to serial port")
        self._serial_port.write(data)

    def _read_bytes(self, data_len: int, block=True):
        # get length of data
        if block == False and self._serial_port.in_waiting < data_len:
            return None

        self._logger.debug(f"Reading {data_len} bytes from serial port")
        return self._serial_port.read(data_len)

    def _write_read_bytes(self, data: bytes):
        self._write_bytes(data)
        time.sleep(0.25) # sleeping (x) s to avoid write and read back errors (rrv change), while this resolved many erros it increased py run time
        return self._read_bytes(len(data))


class ControllerManager:
    def __init__(self, serial_port: str) -> None:
        self._serial_interface = SerialInterface(serial_port)
        pass

    def ping(self) -> None:
        pass

    # Frequency is given in MHz
    def tune_frequency(self, frequency: float) -> float:
        if frequency < 904 or frequency > 927:
            self._serial_interface._logger.warning(
                "The frequency is not in the valid range"
            )
            return 0.0
        if frequency is not int:
            self._serial_interface._logger.warning(
                "The frequency is not valid so it will be rounded to the nearest MHz"
            )

        validFreq = int(frequency)
        freqIndex = validFreq - 904
        indexInBytes = utils.uint8_to_bytes(freqIndex)
        self._serial_interface._write_bytes(b"\x05" + indexInBytes + b"\x00\x00\x00")
        return validFreq

    def read_register(self, register: int) -> int:
        pass
