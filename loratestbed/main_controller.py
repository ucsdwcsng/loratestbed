from loratestbed.controller import SerialInterface
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("-p", "--port", required=True, help="Enter Port Name")
args = vars(ap.parse_args())

PORT = args["port"]

interface = SerialInterface(PORT)

interface._write_read_bytes(b'\x00\x00\x00\x00\x00'); 