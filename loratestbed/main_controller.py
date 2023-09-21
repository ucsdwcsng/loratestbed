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

# main function
def main():
    logging.basicConfig(
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = make_parser()
    args = parser.parse_args()

    device_list = [26]
    # device_list = [25, 26, 28, 29, 32, 33, 34]
    experiment_time_sec = 30
    transmit_interval_msec = 500
    scheduler_interval_mode = 1 # (0: Periodic, 1: Poisson, 2: Periodic with Variance)

    interface = SerialInterface(args.port)
    logging.info("Setting up DeviceManager")
    device_manager = DeviceManager(device_list, interface)
    logging.info(f"Setting experiment time to {experiment_time_sec} seconds")
    device_manager.set_experiment_time_seconds(experiment_time_sec)
    logging.info(f"Setting transmit interval time to {transmit_interval_msec} milliseconds")
    device_manager.set_transmit_interval_milliseconds(transmit_interval_msec)
    logging.info(f"Setting scheduler transmit interval mode to {scheduler_interval_mode}")
    device_manager.set_scheduler_interval_mode(scheduler_interval_mode)
    logging.info("Triggering all devices")
    device_manager.trigger_all_devices()
    logging.info("Waiting for experiment to finish...")
    time.sleep(experiment_time_sec + 3)

'''
    logging.info("Pinging devices")
    pingable_devices = device_manager._ping_devices(device_list)

    assert pingable_devices == device_list, "Not all devices responded to ping"

    logging.info("Reading all result registers")
    result_mat = device_manager.result_registers_from_device()

    for id, device_idx in enumerate(device_list):
        logging.info(f"Device {device_idx} sent {result_mat[id, 0]:.0f} packets")
<<<<<<< Updated upstream

# starts from here
=======
'''

>>>>>>> Stashed changes
if __name__ == "__main__":
    main()
