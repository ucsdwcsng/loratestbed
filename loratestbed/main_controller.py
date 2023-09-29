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
    packet_arrival_model = "poisson"  #("periodic", "poisson")
    transmit_SF = "SF8" #("SF7", "SF8" ... , "SF12, "FSK", SF_RFU")
    receive_SF = "SF8" #("SF7", "SF8" ... , "SF12, "FSK", SF_RFU")
    transmit_BW = "BW125" #("BW125", "BW250", "BW500", BW_RFU")
    receive_BW = "BW125" #("BW125", "BW250", "BW500", BW_RFU")
    transmit_CR = "CR_4_8" #("CR_4_5", "CR_4_6", "CR_4_7", "CR_4_8")
    receive_CR = "CR_4_8" #("CR_4_5", "CR_4_6", "CR_4_7", "CR_4_8")

    interface = SerialInterface(args.port)
    logging.info("Setting up DeviceManager")
    device_manager = DeviceManager(device_list, interface)

    # pre-experiment: updating parameters
    logging.info(f"Setting experiment time to {experiment_time_sec} seconds")
    device_manager.set_experiment_time_seconds(experiment_time_sec)
    logging.info(f"Setting transmit interval time to {transmit_interval_msec} milliseconds")
    device_manager.set_transmit_interval_milliseconds(transmit_interval_msec)
    logging.info(f"Setting scheduler transmit interval mode to {packet_arrival_model}")
    device_manager.set_packet_arrival_model(packet_arrival_model)
    logging.info(f"Setting transmit SF to {transmit_SF} and receive SF to {receive_SF}")
    device_manager.set_transmit_and_receive_SF(transmit_SF, receive_SF)
    logging.info(f"Setting transmit BW to {transmit_BW} and receive BW to {receive_BW}")
    device_manager.set_transmit_and_receive_BW(transmit_BW, receive_BW)
    logging.info(f"Setting transmit CR to {transmit_CR} and receive CR to {receive_CR}")
    device_manager.set_transmit_and_receive_CR(transmit_CR, receive_CR)

    # running experiment
    logging.info("Triggering all devices")
    device_manager.trigger_all_devices()
    logging.info("Waiting for experiment to finish...")
    time.sleep(experiment_time_sec + 3)

    # post-experiment: pinging devices and get results
    logging.info("Pinging devices")
    pingable_devices = device_manager._ping_devices(device_list)
    assert pingable_devices == device_list, "Not all devices responded to ping"
    logging.info("Reading all result registers")
    result_mat = device_manager.result_registers_from_device()
    for id, device_idx in enumerate(device_list):
        logging.info(f"Device {device_idx} sent {result_mat[id, 0]:.0f} packets")
    
# starts from here
if __name__ == "__main__":
    main()
