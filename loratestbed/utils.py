import math


def uint8_to_bytes(value: int) -> bytes:
    # assert value >= 0 and value <= 255

    assert isinstance(value, int), f"Value must be an integer: {value}"
    if value < 0 or value > 255:
        raise ValueError("Value must be between 0 and 255")
    # assert value >= 0 and value <= 255, "Value must be between 0 and 255"

    return value.to_bytes(1, byteorder="big", signed=False)


def bytes_to_uint8(data: bytes) -> int:
    assert len(data) == 1, "Data must be 1 byte long"
    return int.from_bytes(data, byteorder="big", signed=False)


def comp_lora_airtime(PL, SF, CRC, IH, DE, CR, SR, NS):
    """
    Compute Airtime of LoRa (from SX1276 datasheet)
    PL: number of payload bytes
    SF: spreading factor
    CRC: presence of a CRC (0 if absent, 1 if present)
    IH: whether the header is enabled (0 if enabled, 1 if disabled)
    DE: whether low data rate optimization is on (0 if disabled, 1 if enabled)
    CR: the coding rate (1 meaning 4/5 rate, 4 meaning 4/8 rate)
    SR: Sampling Rate
    NS: Number of samples per chirp at sample rate
    """
    max_inp_1 = math.ceil(
        (8 * PL - 4 * SF + 28 + 16 * CRC - 20 * IH) / (4 * (SF - 2 * DE))
    ) * (CR + 4)
    max_inp_2 = 0
    max_val = max(max_inp_1, max_inp_2)

    n_pb = 8 + max_val

    air_time = NS * (n_pb + 12.25) / SR

    return air_time


def compute_packet_time(payload_bytes: int, sf: int, bw_str: str, cr_str: str):
    """_summary_

    Args:
        payload_bytes (int): _description_
        sf (int): _description_
        bw_str (str): _description_
        cr_str (str): _description_

    Raises:
        ValueError: _description_

    Returns:
        _type_: _description_
    """
    bw_khz = float(bw_str[2:])

    if cr_str == "CR_4_8":
        cr = 4
    elif cr_str == "CR_4_5":
        cr = 1
    else:
        raise ValueError(f"Invalid CR value {cr_str}")

    num_samples_per_chirp = 2**sf
    sampling_rate = bw_khz * 1000

    packet_time_sec = comp_lora_airtime(
        payload_bytes, sf, 1, 0, 0, cr, sampling_rate, num_samples_per_chirp
    )

    return packet_time_sec


def get_transmit_interval_msec(
    num_devices: int,
    offered_load_percent: float,
    packet_size_bytes: int,
    transmit_SF: int,
    transmit_BW: int,
    transmit_CR: str,
):
    packet_time_sec: float = compute_packet_time(
        packet_size_bytes, transmit_SF, transmit_BW, transmit_CR
    )

    assert (
        offered_load_percent > 0
    ), f"Offered load must be greater than zero: {offered_load_percent}"

    max_pack_per_sec: float = 1 / packet_time_sec
    net_pack_per_sec: float = max_pack_per_sec * offered_load_percent / 100
    net_pack_per_sec_per_device: float = net_pack_per_sec / float(num_devices)

    transmit_interval_sec: float = 1 / net_pack_per_sec_per_device
    transmit_interval_msec: int = int(transmit_interval_sec * 1000)

    return transmit_interval_msec
