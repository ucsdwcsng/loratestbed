import serial
import sys
import argparse
import time


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

    def read_serial(self, timeout=None):
        start_time = time.time()
        print(f"Reading form gateway serial monitor")
        while True:
            try:
                line = self.ser.readline()
                if line:
                    decoded_line = line.decode("utf-8", errors="replace")
                    self.output.write(decoded_line)
                    self.output.flush()
            except KeyboardInterrupt:
                self.close()
                print("Exiting... (keyboard interrupt)")   
                break         
            if timeout is not None:
                if time.time() - start_time > timeout:
                    self.close()
                    print("Exiting... (timeout)")
                    break

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        if self.file:
            self.file.close()


def run_gateway(baudrate=9600, port=None, filename=None, timeout=None):
    reader = SerialReader(port, baudrate)

    if filename:
        reader.set_output_to_file(filename)
        print(f"Output is written in file: {filename}")
    else:
        reader.set_output_to_console()
        print(f"Output is written to console")

    reader.read_serial(timeout)
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
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        help="Timeout(in sec) to stop reading from serial monitor, e.g: 60 sec",
    )

    args = parser.parse_args()
    run_gateway(args.baudrate, args.port, args.filename, args.timeout)