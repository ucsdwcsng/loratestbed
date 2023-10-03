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

    device_list = [30, 31]
    # device_list = [25, 26, 28, 29, 32, 33, 34]
    interface = SerialInterface(args.port)
    logging.info("Setting up DeviceManager")
    device_manager = DeviceManager(device_list, interface)

    #%% pre-experiment: updating parameters (comment params that are not required to change)
    experiment_time_sec = 30
    # transmit_interval_msec = 500
    # packet_arrival_model = "poisson"  #("periodic", "poisson")
    # transmit_SF = "SF8" #("SF7", "SF8" ... , "SF12, "FSK", SF_RFU")
    # receive_SF = "SF8" #("SF7", "SF8" ... , "SF12, "FSK", SF_RFU")
    transmit_BW = "BW125" #("BW125", "BW250", "BW500", BW_RFU")
    receive_BW = "BW125" #("BW125", "BW250", "BW500", BW_RFU")
    # transmit_CR = "CR_4_8" #("CR_4_5", "CR_4_6", "CR_4_7", "CR_4_8")
    # receive_CR = "CR_4_8" #("CR_4_5", "CR_4_6", "CR_4_7", "CR_4_8")

    device_manager.update_node_params( 
        EXPT_TIME=[experiment_time_sec], 
        # TX_INTERVAL=[transmit_interval_msec], 
        # ARRIVAL_MODEL=[packet_arrival_model], 
        # ARRIVAL_MODEL=[packet_arrival_model, periodic_variance_x10_msec],
        # LORA_SF=[transmit_SF, receive_SF],
        LORA_BW=[transmit_BW, receive_BW],
        # LORA_CR=[transmit_CR, receive_CR],
    )

    #%% running experiment
    logging.info("Triggering all devices")
    device_manager.trigger_all_devices()
    logging.info("Waiting for experiment to finish...")
    time.sleep(experiment_time_sec + 3)

    #%% post-experiment: pinging devices and get results
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
