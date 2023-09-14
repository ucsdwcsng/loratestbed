import argparse
import logging
import pdb
import time

from loratestbed.controller import SerialInterface
from loratestbed.device_manager import DeviceManager


def make_parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--port", required=True, help="Enter Port Name")

    return ap


def main():
    logging.basicConfig(
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = make_parser()
    args = parser.parse_args()

    device_list = [ 33]
    experiment_time = 20

    interface = SerialInterface(args.port)
    logging.info("Setting up DeviceManager")
    device_manager = DeviceManager(device_list, interface)
    logging.info(f"Setting experiment time to {experiment_time} seconds")
    device_manager.set_experiment_time_seconds(experiment_time)
    logging.info("Triggering all devices")
    device_manager.trigger_all_devices()
    logging.info("Waiting for experiment to finish...")
    time.sleep(experiment_time + 3)

    logging.info("Pinging devices")
    pingable_devices = device_manager._ping_devices(device_list)

    assert pingable_devices == device_list, "Not all devices responded to ping"

    logging.info("Reading all result registers")
    result_mat = device_manager.result_registers_from_device()

    for id, device_idx in enumerate(device_list):
        logging.info(f"Device {device_idx} sent {result_mat[id, 0]:.0f} packets")


if __name__ == "__main__":
    main()
