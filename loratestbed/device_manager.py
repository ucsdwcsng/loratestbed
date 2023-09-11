import serial
from typing import List, Tuple
import loratestbed.utils as utils
import logging
import numpy as np
from enum import Enum

from loratestbed.controller import SerialInterface


# Self describing MACRO
REG_ARRAY_LENGTH = 50


class LoRaRegister(Enum):
    # Read/Write
    TX_INTERVAL_GLOBAL = 0  # (ms)
    PACKET_SIZE_BYTES = 1
    EXPERIMENT_TIME_SECONDS = 2
    EXPERIMENT_TIME_MULTIPLIER = 3
    ENABLE_CAD = 4
    DIFS_AS_NUM_OF_CADS = 5
    BACKOFF_CFG1_UNIT_LENGTH_MS = 6
    BACKOFF_CFG2_MAX_MULTIPLIER = 7
    TX_INTERVAL_MULTIPLIER = 8
    SCHEDULER_INTERVAL_MODE = 9  # (0: Periodic, 1: Poisson, 2: Periodic with Variance)

    # Result
    RESULT_COUNTER_BYTE_0 = 10
    RESULT_COUNTER_BYTE_1 = 11
    RESULT_COUNTER_BYTE_2 = 12
    RESULT_BACKOFF_COUNTER_BYTE_0 = 13
    RESULT_BACKOFF_COUNTER_BYTE_1 = 14
    RESULT_BACKOFF_COUNTER_BYTE_2 = 15
    RESULT_LBT_COUNTER_BYTE_0 = 46
    RESULT_LBT_COUNTER_BYTE_1 = 47
    RESULT_LBT_COUNTER_BYTE_2 = 48

    # Configuration
    CONFIG_TXSF_RXSF = 17  # {4bits txsf, 4bits rxsf}
    CONFIG_TXBW_RXBW = 18  # {4bits txbw, 4bits rxbw}
    CONFIG_TXCR_RXCR = 19  # {4bits txcr, 4bits txcr}
    CAD_CONFIG = 20  # {bit 0: Fixed DIFS Size, bit 1: LMAC CSMA}
    LBT_TICKS_X16 = 21  # Listen before talk ticks (x16)
    LBT_MAX_RSSI_S1_T = 22  # Listen before talk max RSSI s1_t
    KILL_CAD_WAIT_TIME = 23  # (0 or 1)

    # Node Index
    NODE_IDX = list(range(24, 45))  # Registers 24 to 44 are for node indexes

    # Other
    PERIODIC_TX_VARIANCE_X10_MS = 45


class DeviceManager:
    def __init__(
        self, device_idxs: List[int], serial_interface: SerialInterface
    ) -> None:
        self._logger = logging.getLogger(__name__)

        self._device_idxs: List[int] = device_idxs
        self._num_devices: int = len(device_idxs)
        self._serial_interface = serial_interface

        # Ping all devices
        self._ping_devices(self._device_idxs)

        # TODO: device states should be initialized by reading the devices themselves
        self._device_states = np.zeros(
            (self._num_devices, REG_ARRAY_LENGTH), dtype=np.uint8
        )
        self._read_all_device_regs(self._device_idxs)

    def _send_message_to_device(self, device_idx: int, message: List[int]):
        # check if device_idx is valid
        if device_idx not in self._device_idxs:
            self._logger.warning(f"Device index {device_idx} not in list of devices")
            return None

        # Check that message is only 3 items long:
        if len(message) != 3:
            self._logger.warning(f"Message {message} is not of length 3")
            return None

        # convert input to bytes:
        device_idx_bytes = utils.uint8_to_bytes(device_idx)
        message_bytes = b"".join([utils.uint8_to_bytes(m) for m in message])

        # Message format: 1, device_idx, message
        read_bytes = self._serial_interface._write_read_bytes(
            b"\x01" + device_idx_bytes + message_bytes
        )

        # Convert each read byte to int:
        read_bytes_int: List[int] = [utils.bytes_to_uint8([b]) for b in read_bytes]
        if read_bytes_int[1] == 255:
            self._logger.critical(f"Readback error, got illegal: {read_bytes_int}")
            return None

        return read_bytes_int

    def _read_device_reg(self, device_idx: int, reg: LoRaRegister) -> int:
        # convert input to bytes:
        message_to_send = [1, reg.value, 0]
        read_bytes_int: List[int] = self._send_message_to_device(
            device_idx, message_to_send
        )
        return read_bytes_int

    def _write_device_reg(self, device_idx: int, reg: LoRaRegister, value: int) -> int:
        # convert input to bytes:
        message_to_send = [2, reg.value, value]
        read_bytes_int: List[int] = self._send_message_to_device(
            device_idx, message_to_send
        )
        if (read_bytes_int is not None) and read_bytes_int[-1] != value:
            self._logger.critical(f"Tried to write {value}, got {read_bytes_int[-1]}")
        return read_bytes_int

    def _ping_devices(self, device_idxs: List[int]) -> None:
        # check if list, if not make into list:
        if not isinstance(device_idxs, list):
            device_idxs = [device_idxs]

        for device_idx in device_idxs:
            ret_list = self._send_message_to_device(device_idx, [0, 0, 0])
            # TODO: logic to update device list if a device is not ping-able
            if ret_list is None:
                self._logger.critical(f"Device {device_idx} did not respond to ping")

    def _read_all_device_regs(self, device_idxs: List[int]):
        if not isinstance(device_idxs, list):
            device_idxs = [device_idxs]
        for id, device_idx in enumerate(device_idxs):
            for reg_id in LoRaRegister:
                ret_int_list = self._read_device_reg(device_idx, reg_id)
                self._device_states[id, reg_id.value] = ret_int_list[-1]
