import serial
import signal
import sys
import argparse


class SerialReader:
    def __init__(self, port, baudrate=9600, timeout=1):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        self.output = sys.stdout
        self.file = None

    def set_output_to_console(self):
        if self.file:
            self.file.close()
        self.output = sys.stdout

    def set_output_to_file(self, filename):
        if self.file:
            self.file.close()
        self.file = open(filename, "w", encoding="utf-8")
        self.output = self.file

    def read_serial(self):
        try:
            while True:
                line = self.ser.readline()
                if line:
                    decoded_line = line.decode("utf-8", errors="replace")
                    self.output.write(decoded_line)
                    self.output.flush()
        except KeyboardInterrupt:
            print("Exiting...")

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        if self.file:
            self.file.close()


def sigint_handler(signal, frame):
    global reader
    reader.close()
    sys.exit(0)


def run_gateway(baudrate=9600, port=None, filename=None):
    reader = SerialReader(port, baudrate)

    if filename:
        reader.set_output_to_file(filename)
    else:
        reader.set_output_to_console()

    signal.signal(signal.SIGINT, sigint_handler)

    reader.read_serial()
    reader.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Read data from a serial interface and write to a given output."
    )
    parser.add_argument(
        "-b",
        "--baudrate",
        type=int,
        default=2000000,
        help="Baud rate for the serial interface. Default is 2000000.",
    )
    parser.add_argument(
        "-p",
        "--port",
        required=True,
        help="Port for the serial interface, e.g., /dev/ttyUSB0.",
    )
    parser.add_argument(
        "-f",
        "--filename",
        type=str,
        help="Filename to output data. If not provided, data is written to stdout.",
    )

    args = parser.parse_args()
    run_gateway(args.baudrate, args.port, args.filename)
