import argparse
import logging

from loratestbed.controller import SerialInterface
from loratestbed.device_manager import DeviceManager


def main():
    logging.basicConfig(
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        level=logging.DEBUG,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--port", required=True, help="Enter Port Name")
    args = vars(ap.parse_args())
    PORT = args["port"]
    interface = SerialInterface(PORT)

    # # Create a message 1, 33, 0,0,0
    # message = b"\x01\x21\x00\x00\x00"

    # # read_bytes = interface._write_read_bytes(b"\x00\x00\x00\x00\x00")
    # logging.info(f"Writing {message} to serial port")
    # read_bytes = interface._write_read_bytes(message)

    # logging.info(f"Read {read_bytes} from serial port")
    device_manager = DeviceManager([33], interface)
    device_manager._ping_devices(33)


if __name__ == "__main__":
    main()
