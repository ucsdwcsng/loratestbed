import argparse
import logging

from loratestbed.controller import SerialInterface


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

    read_bytes = interface._write_read_bytes(b"\x00\x00\x00\x00\x00")

    logging.info(f"Read {read_bytes} from serial port")


if __name__ == "__main__":
    main()
