def uint8_to_bytes(value: int) -> bytes:
    # assert value >= 0 and value <= 255

    assert isinstance(value, int), "Value must be an integer"
    if value < 0 or value > 255:
        raise ValueError("Value must be between 0 and 255")
    # assert value >= 0 and value <= 255, "Value must be between 0 and 255"

    return value.to_bytes(1, byteorder="big", signed=False)


def bytes_to_uint8(data: bytes) -> int:
    assert len(data) == 1, "Data must be 1 byte long"
    return int.from_bytes(data, byteorder="big", signed=False)
