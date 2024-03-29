import serial
from typing import Any, List, Tuple
import loratestbed.utils as utils
import logging
import numpy as np
from enum import Enum
import time
import pandas as pd
import pdb
from loratestbed.controller import SerialInterface


# Self describing MACRO
REG_ARRAY_LENGTH = 64


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

    # FSMA
    ENABLE_FSMA = 49
    LBT_MIN_RSSI_S1_T = 50
    ENABLE_EXPONENTIAL_BACKOFF = 51


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
        self._ping_limit = 5  # ping for max 5 times

        # Device states initialized by reading the devices themselves
        self._device_states = np.zeros(
            (self._num_devices, REG_ARRAY_LENGTH), dtype=np.uint8
        )
        # self._read_all_device_regs(self._device_idxs)

    def _message_to_device(self, device_idx: int, message: List[int]):
        # check if device_idx is valid
        if device_idx not in self._device_idxs and device_idx != 255:
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
        data_to_send = b"\x01" + device_idx_bytes + message_bytes

        repeat_condition = True
        ping_node_again = self._ping_limit
        while repeat_condition and ping_node_again > 0:
            read_bytes = self._serial_interface._write_read_bytes(data_to_send)
            ping_node_again -= 1
            # 0th (dummy 1) and 2nd (operation type) indices should always be same
            repeat_condition = (
                (read_bytes is None)
                or (read_bytes[0] != data_to_send[0])
                or (read_bytes[2] != data_to_send[2])
            )

        # Convert each read byte to int:
        read_bytes_int: List[int] = [utils.bytes_to_uint8([b]) for b in read_bytes]
        if read_bytes_int[1] == 255 and device_idx != 255:
            self._logger.critical(f"Readback error, got illegal: {read_bytes_int}")
            return message

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
        ping_limit = 5  # ping for max 5 times
        if not isinstance(device_idxs, list):
            device_idxs = [device_idxs]
        for id, device_idx in enumerate(device_idxs):
            for reg_id in LoRaRegister:
                ret_int_list = self._device_reg(device_idx, reg_id)
                if ret_int_list is None:
                    ret_int_list = [0]
                    self._logger.warning(
                        f"Device {device_idx}'s register {reg_id} did not respond, default 0"
                    )
                self._device_states[id, reg_id.value] = ret_int_list[-1]

    def disable_all_devices(self):
        # Disable all devices by broadcasting 0 experiment time
        self._write_device_reg(255, LoRaRegister.EXPERIMENT_TIME_SECONDS, 0)
        self._write_device_reg(255, LoRaRegister.EXPERIMENT_TIME_SECONDS, 0)

    def trigger_all_devices(self):
        self._message_to_device(255, [10, 0, 0])
        self._message_to_device(255, [10, 0, 0])
        return self._message_to_device(255, [10, 0, 0])

    # Setting total experiment time in seconds
    def _set_experiment_time_seconds(self, time_sec: int):
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

    # Setting transmit time interval in milliseconds
    def _set_transmit_interval_milliseconds(self, time_interval_msec: int):
        tx_interval_multiplier: int = time_interval_msec // 256 + 1
        tx_interval_milliseconds: int = int(time_interval_msec / tx_interval_multiplier)

        for device_idx in self._device_idxs:
            self._write_device_reg(
                device_idx, LoRaRegister.TX_INTERVAL_GLOBAL, tx_interval_milliseconds
            )
            self._write_device_reg(
                device_idx,
                LoRaRegister.TX_INTERVAL_MULTIPLIER,
                tx_interval_multiplier,
            )

    def set_mac_protocol(
        self, protocol: str, min_backoff_ms: int = 12, max_backoff_ms: int = 64 * 12
    ):
        # Below is for LMAC
        # [CAD_REG, DIFS, BACKOFF TIMEms, MAX BACKOFFMULT, CADTYPECNFG, LBT_TICKS, LBT_MAX_RSSI]
        # expt_params.cad_cnfg_cell = {repmat([1 2 12 64 0 8 -90],com_node_num,1),...
        if not isinstance(protocol, str):
            raise ValueError("Input must be a string")
        isCSMA = protocol.lower() == "csma"
        isALOHA = protocol.lower() == "aloha"
        isFSMA = protocol.lower() == "fsma"

        backoff_multiplier = max_backoff_ms // min_backoff_ms

        for device_idx in self._device_idxs:
            if isFSMA:
                # FSMA specific
                self._write_device_reg(device_idx, LoRaRegister.ENABLE_FSMA, 1)
                self._write_device_reg(
                    device_idx,
                    LoRaRegister.LBT_MIN_RSSI_S1_T,
                    int(np.int8(-116).view(np.uint8)),
                )
                self._write_device_reg(
                    device_idx, LoRaRegister.ENABLE_EXPONENTIAL_BACKOFF, 0
                )

                # CAD specific
                self._write_device_reg(device_idx, LoRaRegister.ENABLE_CAD, 1)
                self._write_device_reg(device_idx, LoRaRegister.CAD_CONFIG, 0)
                self._write_device_reg(device_idx, LoRaRegister.DIFS_AS_NUM_OF_CADS, 2)
                self._write_device_reg(
                    device_idx, LoRaRegister.BACKOFF_CFG1_UNIT_LENGTH_MS, min_backoff_ms
                )
                self._write_device_reg(
                    device_idx,
                    LoRaRegister.BACKOFF_CFG2_MAX_MULTIPLIER,
                    backoff_multiplier,
                )
                self._write_device_reg(device_idx, LoRaRegister.LBT_TICKS_X16, 8)
                self._write_device_reg(device_idx, LoRaRegister.KILL_CAD_WAIT_TIME, 1)
            elif isCSMA:
                # set CAD reg to 1:
                self._write_device_reg(device_idx, LoRaRegister.ENABLE_CAD, 1)
                self._write_device_reg(device_idx, LoRaRegister.CAD_CONFIG, 0)
                self._write_device_reg(device_idx, LoRaRegister.DIFS_AS_NUM_OF_CADS, 3)
                self._write_device_reg(
                    device_idx, LoRaRegister.BACKOFF_CFG1_UNIT_LENGTH_MS, min_backoff_ms
                )
                self._write_device_reg(
                    device_idx,
                    LoRaRegister.BACKOFF_CFG2_MAX_MULTIPLIER,
                    backoff_multiplier,
                )
                self._write_device_reg(device_idx, LoRaRegister.LBT_TICKS_X16, 8)
                self._write_device_reg(
                    device_idx,
                    LoRaRegister.LBT_MAX_RSSI_S1_T,
                    int(np.int8(-90).view(np.uint8)),
                )
                self._write_device_reg(device_idx, LoRaRegister.KILL_CAD_WAIT_TIME, 1)
                self._write_device_reg(device_idx, LoRaRegister.ENABLE_FSMA, 0)
            elif isALOHA:
                self._write_device_reg(device_idx, LoRaRegister.ENABLE_CAD, 0)
                self._write_device_reg(device_idx, LoRaRegister.ENABLE_FSMA, 0)
            else:
                raise ValueError(f"{protocol} is not supported")

    # Setting packet arrival model at node: periodic or poisson (if periodic add optional variance)
    def _set_packet_arrival_model(self, arrival_model: str, variance_ms=None):
        if not isinstance(arrival_model, str):
            raise ValueError("Input must be a string")

        isPoisson = arrival_model.lower() == "poisson"
        isPeriodic = arrival_model.lower() == "periodic"
        if isPoisson:
            scheduler_interval_mode = 1
            if variance_ms is not None:
                self._logger.warning(
                    f"packet arrival mode is poisson, ignoring variance {variance_ms} ms"
                )
        elif isPeriodic:
            if variance_ms is None:
                scheduler_interval_mode = 0
            else:
                scheduler_interval_mode = 2
                self._set_packet_arrival_periodic_variance(
                    variance_ms,
                )
        else:
            raise ValueError("Input string must be either 'poisson' or 'periodic'")

        for device_idx in self._device_idxs:
            self._write_device_reg(
                device_idx,
                LoRaRegister.SCHEDULER_INTERVAL_MODE,
                scheduler_interval_mode,
            )

    # Setting packet arrival mode - periodic variance in ms
    def _set_packet_arrival_periodic_variance(self, variance_ms: int):
        if not isinstance(variance_ms, int):
            raise ValueError("Input must be an integer")

        if (variance_ms < 0) or (variance_ms > 2550):
            raise ValueError("Input integer must be between 0 and 2550")

        # we can only set variance in multiples of x10 ms
        variance_x10_ms = variance_ms // 10  # give only integer value
        if variance_ms % 10 != 0:
            self._logger.warning(
                f"variance_ms {variance_ms} ms is not multiple of 10, rounded off to {variance_x10_ms*10} ms"
            )

        for device_idx in self._device_idxs:
            self._write_device_reg(
                device_idx, LoRaRegister.PERIODIC_TX_VARIANCE_X10_MS, variance_x10_ms
            )

    # Set SF for transmit and receive modes
    def _set_transmit_and_receive_SF(self, transmit_SF: str, receive_SF: str):
        if not isinstance(transmit_SF, str) or not isinstance(receive_SF, str):
            raise ValueError("Both inputs must be a string")

        transmit_SF_mode = self._convert_SF_string_to_mode(transmit_SF)
        receive_SF_mode = self._convert_SF_string_to_mode(receive_SF)
        config_txSF_rxSF = (transmit_SF_mode << 4) + receive_SF_mode
        self._logger.debug(
            f"setting SF transmit mode: {transmit_SF_mode}, SF receive mode: {receive_SF_mode}, combined SF mode(8 bits): {config_txSF_rxSF}"
        )

        # updating CONFIG_TXSF_RXSF register
        for device_idx in self._device_idxs:
            self._write_device_reg(
                device_idx, LoRaRegister.CONFIG_TXSF_RXSF, config_txSF_rxSF
            )

    # internal function to convert SF string to SF mode
    def _convert_SF_string_to_mode(self, SF_string):
        SF_dictionary = {
            "FSK": 0,
            "SF7": 1,
            "SF8": 2,
            "SF9": 3,
            "SF10": 4,
            "SF11": 5,
            "SF12": 6,
            "SF_RFU": 7,
        }

        SF_UP_string = SF_string.upper()  # to make input SF string case insensitive
        if SF_UP_string in SF_dictionary:
            return SF_dictionary[SF_UP_string]
        else:
            possible_SF_strings = ",".join(SF_dictionary.keys())
            raise ValueError(
                f"Given SF string '{SF_string}' not in valid SF strings: [{possible_SF_strings}]"
            )

    # Set BW for transmit and receive modes
    def _set_transmit_and_receive_BW(self, transmit_BW: str, receive_BW: str):
        if not isinstance(transmit_BW, str) or not isinstance(receive_BW, str):
            raise ValueError("Both inputs must be a string")

        transmit_BW_mode = self._convert_BW_string_to_mode(transmit_BW)
        receive_BW_mode = self._convert_BW_string_to_mode(receive_BW)
        config_txBW_rxBW = (transmit_BW_mode << 4) + receive_BW_mode
        self._logger.debug(
            f"setting BW transmit mode: {transmit_BW_mode}, BW receive mode: {receive_BW_mode}, combined BW mode(8 bits): {config_txBW_rxBW}"
        )

        # updating CONFIG_TXBW_RXBW register
        for device_idx in self._device_idxs:
            self._write_device_reg(
                device_idx, LoRaRegister.CONFIG_TXBW_RXBW, config_txBW_rxBW
            )

    # internal function to convert BW string to BW mode
    def _convert_BW_string_to_mode(self, BW_string):
        BW_dictionary = {
            "BW125": 0,
            "BW250": 1,
            "BW500": 2,
            "BW_RFU": 3,
        }

        BW_UP_string = BW_string.upper()  # to make input BW string case insensitive
        if BW_UP_string in BW_dictionary:
            return BW_dictionary[BW_UP_string]
        else:
            possible_BW_strings = ",".join(BW_dictionary.keys())
            raise ValueError(
                f"Given BW string '{BW_string}' not in valid BW strings: [{possible_BW_strings}]"
            )

    def set_packet_size_bytes(self, packet_size_bytes: int):
        for device_idx in self._device_idxs:
            self._write_device_reg(
                device_idx, LoRaRegister.PACKET_SIZE_BYTES, packet_size_bytes
            )

    # Set CR for transmit and receive modes
    def _set_transmit_and_receive_CR(self, transmit_CR: str, receive_CR: str):
        if not isinstance(transmit_CR, str) or not isinstance(receive_CR, str):
            raise ValueError("Both inputs must be a string")

        transmit_CR_mode = self._convert_CR_string_to_mode(transmit_CR)
        receive_CR_mode = self._convert_CR_string_to_mode(receive_CR)
        config_txCR_rxCR = (transmit_CR_mode << 4) + receive_CR_mode
        self._logger.debug(
            f"setting CR transmit mode: {transmit_CR_mode}, CR receive mode: {receive_CR_mode}, combined CR mode(8 bits): {config_txCR_rxCR}"
        )

        # updating CONFIG_TXCR_RXCR register
        for device_idx in self._device_idxs:
            self._write_device_reg(
                device_idx, LoRaRegister.CONFIG_TXCR_RXCR, config_txCR_rxCR
            )

    # internal function to convert CR string to CR mode
    def _convert_CR_string_to_mode(self, CR_string):
        CR_dictionary = {
            "CR_4_5": 0,
            "CR_4_6": 1,
            "CR_4_7": 2,
            "CR_4_8": 3,
        }

        CR_UP_string = CR_string.upper()  # to make input CR string case insensitive
        if CR_UP_string in CR_dictionary:
            return CR_dictionary[CR_UP_string]
        else:
            possible_CR_strings = ",".join(CR_dictionary.keys())
            raise ValueError(
                f"Given CR string '{CR_string}' not in valid CR strings: [{possible_CR_strings}]"
            )

    def update_node_params(self, **kwargs):
        # Configurable node params
        configurable_node_params_list = {
            "EXPT_TIME": self._set_experiment_time_seconds,
            "TX_INTERVAL": self._set_transmit_interval_milliseconds,
            "ARRIVAL_MODEL": self._set_packet_arrival_model,
            "LORA_SF": self._set_transmit_and_receive_SF,
            "LORA_BW": self._set_transmit_and_receive_BW,
            "LORA_CR": self._set_transmit_and_receive_CR,
        }

        for node_param, args in kwargs.items():
            node_param_up = node_param.upper()  # This makes input case in-sensitive
            if node_param_up in configurable_node_params_list:
                function = configurable_node_params_list[node_param_up]
                # check if the number of args are valid for the respective function
                if node_param_up == "EXPT_TIME":
                    self._logger.info(f"Setting experiment time to {args[0]} seconds")
                    assert (
                        len(args) == 1
                    ), "Changing 'experiment time' only requires one input (time in seconds)"
                elif node_param_up == "TX_INTERVAL":
                    self._logger.info(
                        f"Setting transmit interval time to {args[0]} milliseconds"
                    )
                    assert (
                        len(args) == 1
                    ), "Changing 'transmit interval' only requires one input (time in seconds)"
                elif node_param_up == "ARRIVAL_MODEL":
                    self._logger.info(
                        f"Setting scheduler transmit interval mode to {args[0]}"
                    )
                    assert (
                        len(args) == 1 or len(args) == 2
                    ), "Changing 'arrival model' needs one manadate input (model type) and an optional input for periodic type (variance)"
                elif node_param_up == "LORA_SF":
                    self._logger.info(
                        f"Setting transmit SF to {args[0]} and receive SF to {args[1]}"
                    )
                    assert (
                        len(args) == 2
                    ), "Changing 'LoRa SF' requires two string inputs ('transmit SF' and 'receive SF')"
                elif node_param_up == "LORA_BW":
                    self._logger.info(
                        f"Setting transmit BW to {args[0]} and receive BW to {args[1]}"
                    )
                    assert (
                        len(args) == 2
                    ), "Changing 'LoRa BW' requires two string inputs ('transmit BW' and 'receive BW')"
                elif node_param_up == "LORA_CR":
                    self._logger.info(
                        f"Setting transmit CR to {args[0]} and receive CR to {args[1]}"
                    )
                    assert (
                        len(args) == 2
                    ), "Changing 'LoRa CR requires two string inputs ('transmit CR' and 'receive CR')"
                function(*args)
            else:
                raise ValueError(
                    f"Given node param '{node_param}' not in configurable node params list: [{configurable_node_params_list}]"
                )

    def results(self):
        results = self._result_registers_from_device()
        column_names = [
            "NodeAddress",
            "TransmittedPackets",
            "BackoffCounter",
            "LBTCounter",
        ]
        result_df: pd.Dataframe = pd.DataFrame(results, columns=column_names)
        result_df.reset_index(drop=True, inplace=True)
        return result_df

    def _result_registers_from_device(self):
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

        results = np.zeros(
            (self._num_devices, len(result_registers) + 1), dtype=np.int32
        )

        for id, device_idx in enumerate(self._device_idxs):
            results[id, 0] = int(device_idx)
            for reg_series, reg_id in enumerate(result_registers):
                ret_int_list = self._device_reg(device_idx, reg_id)
                if ret_int_list is None:
                    ret_int_list = [0]
                    self._logger.warning(
                        f"Device {device_idx}'s register {reg_id} did not respond, default 0"
                    )
                results[id, reg_series + 1] = ret_int_list[-1]

        # Add the byte registers together to get the full result
        for i in range(1, 10, 3):
            results[:, i] = (
                results[:, i] + 256 * results[:, i + 1] + 256 * 256 * results[:, i + 2]
            )

        results[:, 1:4:1] = results[:, 1::3]

        return results[:, :4]
