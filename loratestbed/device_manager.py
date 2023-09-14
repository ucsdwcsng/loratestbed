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

    # # Node Index
    # NODE_IDX = list(range(24, 45))  # Registers 24 to 44 are for node indexes
    # Node Indices
    NODE_IDX_0 = 24
    NODE_IDX_1 = 25
    NODE_IDX_2 = 26
    NODE_IDX_3 = 27
    NODE_IDX_4 = 28
    NODE_IDX_5 = 29
    NODE_IDX_6 = 30
    NODE_IDX_7 = 31
    NODE_IDX_8 = 32
    NODE_IDX_9 = 33
    NODE_IDX_10 = 34
    NODE_IDX_11 = 35
    NODE_IDX_12 = 36
    NODE_IDX_13 = 37
    NODE_IDX_14 = 38
    NODE_IDX_15 = 39
    NODE_IDX_16 = 40
    NODE_IDX_17 = 41
    NODE_IDX_18 = 42
    NODE_IDX_19 = 43
    NODE_IDX_20 = 44

    # Other
    PERIODIC_TX_VARIANCE_X10_MS = 45


RESULT_REGISTERS = [
    LoRaRegister.RESULT_COUNTER_BYTE_0,
    LoRaRegister.RESULT_COUNTER_BYTE_1,
    LoRaRegister.RESULT_COUNTER_BYTE_2,
    LoRaRegister.RESULT_BACKOFF_COUNTER_BYTE_0,
    LoRaRegister.RESULT_BACKOFF_COUNTER_BYTE_1,
    LoRaRegister.RESULT_BACKOFF_COUNTER_BYTE_2,
    LoRaRegister.RESULT_LBT_COUNTER_BYTE_0,
    LoRaRegister.RESULT_LBT_COUNTER_BYTE_1,
    LoRaRegister.RESULT_LBT_COUNTER_BYTE_2,
]


class DeviceManager:
    def __init__(
        self, device_idxs: List[int], serial_interface: SerialInterface
    ) -> None:
        self._logger = logging.getLogger(__name__)

        self._device_idxs: List[int] = device_idxs
        self._num_devices: int = len(device_idxs)
        self._serial_interface = serial_interface

        # Device states initialized by reading the devices themselves
        self._device_states = np.zeros(
            (self._num_devices, REG_ARRAY_LENGTH), dtype=np.uint8
        )
        self._read_all_device_regs(self._device_idxs)

    def _message_to_device(self, device_idx: int, message: List[int]):
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
        if read_bytes_int[1] == 255 and device_idx != 255:
            self._logger.critical(f"Readback error, got illegal: {read_bytes_int}")
            return None

        return read_bytes_int

    def _device_reg(self, device_idx: int, reg: LoRaRegister) -> int:
        # convert input to bytes:
        message_to_send = [1, reg.value, 0]
        read_bytes_int: List[int] = self._message_to_device(device_idx, message_to_send)
        return read_bytes_int

    def _clear_device_reg(self, device_idx: int, reg: LoRaRegister) -> int:
        # Readback value from register, then set it to zero (clear)
        if reg not in RESULT_REGISTERS:
            self._logger.warning(f"Register {reg} cannot be cleared, aborting")
            return None

        message_to_send = [5, reg.value, 0]
        read_bytes_int: List[int] = self._message_to_device(device_idx, message_to_send)
        return read_bytes_int

    def _write_device_reg(self, device_idx: int, reg: LoRaRegister, value: int) -> int:
        # convert input to bytes:
        message_to_send = [2, reg.value, value]
        read_bytes_int: List[int] = self._message_to_device(device_idx, message_to_send)
        if (read_bytes_int is not None) and read_bytes_int[-1] != value:
            self._logger.critical(f"Tried to write {value}, got {read_bytes_int[-1]}")
        return read_bytes_int

    def _ping_devices(self, device_idxs: List[int]) -> None:
        # check if list, if not make into list:
        if not isinstance(device_idxs, list):
            device_idxs = [device_idxs]
        pingable_devices = []
        for device_idx in device_idxs:
            ret_list = self._message_to_device(device_idx, [0, 0, 0])
            # TODO: logic to update device list if a device is not ping-able
            if ret_list is None:
                self._logger.critical(f"Device {device_idx} did not respond to ping")
            else:
                pingable_devices.append(device_idx)
        return pingable_devices

    def _read_all_device_regs(self, device_idxs: List[int]):
        if not isinstance(device_idxs, list):
            device_idxs = [device_idxs]
        for id, device_idx in enumerate(device_idxs):
            for reg_id in LoRaRegister:
                ret_int_list = self._device_reg(device_idx, reg_id)
                self._device_states[id, reg_id.value] = ret_int_list[-1]

    def disable_all_devices(self):
        # Disable all devices by broadcasting 0 experiment time
        self._write_device_reg(255, LoRaRegister.EXPERIMENT_TIME_SECONDS, 0)
        self._write_device_reg(255, LoRaRegister.EXPERIMENT_TIME_SECONDS, 0)

    def trigger_all_devices(self):
        self._message_to_device(255, [10, 0, 0])
        self._message_to_device(255, [10, 0, 0])
        return self._message_to_device(255, [10, 0, 0])

    def set_experiment_time_seconds(self, time_sec: int):
        expt_time_multiplier: int = time_sec // 256 + 1
        expt_time_seconds: int = int(time_sec / expt_time_multiplier)

        for device_idx in self._device_idxs:
            self._write_device_reg(
                device_idx, LoRaRegister.EXPERIMENT_TIME_SECONDS, expt_time_seconds
            )
            self._write_device_reg(
                device_idx,
                LoRaRegister.EXPERIMENT_TIME_MULTIPLIER,
                expt_time_multiplier,
            )

    def result_registers_from_device(self):
        result_registers = [
            LoRaRegister.RESULT_COUNTER_BYTE_0,
            LoRaRegister.RESULT_COUNTER_BYTE_1,
            LoRaRegister.RESULT_COUNTER_BYTE_2,
            LoRaRegister.RESULT_BACKOFF_COUNTER_BYTE_0,
            LoRaRegister.RESULT_BACKOFF_COUNTER_BYTE_1,
            LoRaRegister.RESULT_BACKOFF_COUNTER_BYTE_2,
            LoRaRegister.RESULT_LBT_COUNTER_BYTE_0,
            LoRaRegister.RESULT_LBT_COUNTER_BYTE_1,
            LoRaRegister.RESULT_LBT_COUNTER_BYTE_2,
        ]

        results = np.zeros((self._num_devices, len(result_registers)), dtype=np.float32)

        for id, device_idx in enumerate(self._device_idxs):
            for reg_id in result_registers:
                # TODO: make this read clear
                ret_int_list = self._device_reg(device_idx, reg_id)
                results[id, reg_id.value] = ret_int_list[-1]

        # Add the byte registers together to get the full result
        for i in range(0, 9, 3):
            results[:, i] = (
                results[:, i] + 256 * results[:, i + 1] + 256 * 256 * results[:, i + 2]
            )

        return results[:, ::3]
