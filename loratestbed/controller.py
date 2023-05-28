import serial
from typing import List, Tuple
import logging


class Controller:
    def __init__(self, serial_path: str, baud_rate: int = 115200) -> None:
        # Set up Logger
        self._logger = logging.getLogger(__name__)

        # Set up serial port
        self._logger.info(
            f"Setting up serial port at {serial_path} with baud rate {baud_rate}"
        )
        self._serial_port = serial.Serial(serial_path, baud_rate)
        self._logger.info(f"Connected")

    def _write_read_n_bytes(self, data: bytes) -> bytes:
        # get length of data
        data_len = len(data)
        self._logger.debug(f"Writing {data_len} bytes to serial port")
        self._serial_port.write(data)
        return self._serial_port.read(data_len)
