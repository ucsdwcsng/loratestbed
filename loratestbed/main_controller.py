import argparse
import logging

from loratestbed.controller import SerialInterface
from loratestbed.device_manager import DeviceManager


def main():
    logging.basicConfig(
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--port", required=True, help="Enter Port Name")
    args = vars(ap.parse_args())
    PORT = args["port"]
    interface = SerialInterface(PORT)

    device_manager = DeviceManager([26, 33], interface)
    # device_manager._ping_devices(33)


if __name__ == "__main__":
    main()
