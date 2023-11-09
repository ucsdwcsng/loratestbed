from loratestbed.utils import (
    uint8_to_bytes,
    bytes_to_uint8,
    compute_packet_time,
    get_transmit_interval_msec,
)


def test_uint8_to_bytes():
    assert uint8_to_bytes(0) == b"\x00"
    assert uint8_to_bytes(1) == b"\x01"
    assert uint8_to_bytes(24) == b"\x18"
    assert uint8_to_bytes(100) == b"\x64"
    assert uint8_to_bytes(255) == b"\xff"

    try:
        uint8_to_bytes(-1)
        assert False
    except ValueError:
        assert True


def test_uint8_two_way():
    for i in range(0, 256):
        assert bytes_to_uint8(uint8_to_bytes(i)) == i


def test_transmit_interval():
    packet_size_bytes = 16
    sf_val = 8
    bw_str = "BW125"
    cr_str = "CR_4_8"

    print()

    interval_4_dev_100pc = get_transmit_interval_msec(
        4, 100, packet_size_bytes, sf_val, bw_str, cr_str
    )
    interval_4_dev_10pc = get_transmit_interval_msec(
        4, 10, packet_size_bytes, sf_val, bw_str, cr_str
    )
    interval_40_dev_100pc = get_transmit_interval_msec(
        40, 100, packet_size_bytes, sf_val, bw_str, cr_str
    )
    interval_40_dev_10pc = get_transmit_interval_msec(
        40, 10, packet_size_bytes, sf_val, bw_str, cr_str
    )

    assert interval_4_dev_100pc == int(interval_4_dev_10pc / 10)
    assert interval_40_dev_100pc == int(interval_40_dev_10pc / 10)
    assert interval_4_dev_100pc == int(interval_40_dev_100pc / 10)

    transmit_interval_msec = get_transmit_interval_msec(
        10,
        100,
        packet_size_bytes,
        sf_val,
        bw_str,
        cr_str,
    )

    print(
        f"10 devices, {packet_size_bytes} byte payload, [SF{sf_val}|{bw_str}|{cr_str}] \nOffered load: {100}%, Transmit interval: {transmit_interval_msec} msec"
    )
