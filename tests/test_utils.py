from loratestbed.utils import uint8_to_bytes, bytes_to_uint8


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
