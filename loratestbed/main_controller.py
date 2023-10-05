import argparse
import logging
import pdb
import time
import csv
import numpy as np
from threading import Thread
from datetime import datetime

from loratestbed.controller import SerialInterface
from loratestbed.device_manager import DeviceManager
from loratestbed.main_gateway import run_gateway
from loratestbed.experiment_logbook import logbook_add_entry

def make_parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--controller_port", required=True, help="Enter Port Name")
    ap.add_argument("-p2", "--gateway_port", required=True, help="Enter Port Name")

    return ap

def run_experiment(device_manager: DeviceManager, experiment_time_sec: int, control_filename: str, gateway_port, gateway_filename=None, gateway_timeout=None, gateway_baudrate=9600):
    thread1 = Thread(target=run_controller,args=(device_manager, experiment_time_sec, control_filename))
    thread2 = Thread(target=run_gateway, args=(gateway_baudrate, gateway_port, gateway_filename, gateway_timeout)) 

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()


def run_controller(device_manager: DeviceManager, experiment_time_sec: int, control_filename = None):
    ## Trigger all nodes
    logging.info("Triggering all devices")
    device_manager.trigger_all_devices()
    logging.info("Waiting for experiment to finish...")
    time.sleep(experiment_time_sec + 3)

    ## pinging devices, get stastics from nodes and save in given controller_file
    logging.info("Pinging devices")
    device_list = device_manager.get_device_indicies()
    pingable_devices = device_manager._ping_devices(device_list)
    assert pingable_devices == device_list, "Not all devices responded to ping"
    logging.info("Reading all result registers")
    result_mat = device_manager.result_registers_from_device()

    # if given filename, write into the file else show result in logs (info)
    if control_filename:
        with open(control_filename, mode="w", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            result_mat_with_device_id = np.hstack((np.array(device_list).reshape(-1,1),result_mat))
            for row in result_mat_with_device_id:
                csv_writer.writerow(row)
        logging.info(f"Result data is written in the given file ({control_filename}).")
    else:
        for id, device_idx in enumerate(device_list):
            logging.info(f"Device {device_idx} sent {result_mat[id, 0]:.0f} packets")

# main function
def main():
    logging.basicConfig(
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = make_parser()
    args = parser.parse_args()

    device_list = [30,31,34]
    # device_list = [25, 26, 28, 29, 32, 33, 34]
    interface = SerialInterface(args.controller_port)
    logging.info("Setting up DeviceManager")
    device_manager = DeviceManager(device_list, interface)
    device_manager.disable_all_devices()# Disable all devices, later only set experiment time to the desired nodes

    # initialzing node parameters
    node_params = { 
        "experiment_time_sec": 30,
        "transmit_interval_msec": 1000,
        "packet_arrival_model": "POISSON",  #("PERIODIC", "POISSON")
        "periodic_variance_x10_msec": 0,
        "transmit_SF": "SF8", "receive_SF": "SF8", #("SF7", "SF8" ... , "SF12, "FSK", SF_RFU")
        "transmit_BW": "BW125", "receive_BW": "BW125", #("BW125", "BW250", "BW500", BW_RFU")
        "transmit_CR": "CR_4_8", "receive_CR": "CR_4_8", #("CR_4_5", "CR_4_6", "CR_4_7", "CR_4_8")
        }

    # updating parameters (comment params that are not required to change)
    device_manager.update_node_params( 
        EXPT_TIME = [node_params["experiment_time_sec"]], 
        TX_INTERVAL = [node_params["transmit_interval_msec"]], 
        ARRIVAL_MODEL = [node_params["packet_arrival_model"]], 
        # ARRIVAL_MODEL=[node_params["packet_arrival_model"], node_params["periodic_variance_x10_msec"]],
        LORA_SF=[node_params["transmit_SF"], node_params["receive_SF"]],
        LORA_BW=[node_params["transmit_BW"], node_params["receive_BW"]],
        LORA_CR=[node_params["transmit_CR"], node_params["receive_CR"]],
    )

    # runnning experiment
    folder_name = "data_files_local"
    current_time = datetime.now()
    controller_filename = f"{folder_name}/controller_{current_time.strftime('%Y_%m_%d_%H_%M_%S')}.csv"
    logbook_filename = f"{folder_name}/experiment_logbook.csv"
    gateway_filename = f"{folder_name}/gateway_{current_time.strftime('%Y_%m_%d_%H_%M_%S')}.csv"
    gateway_port = args.gateway_port
    gateway_baudrate = 2000000
    gateway_timeout = node_params["experiment_time_sec"]+10

    #run_gateway(gateway_baudrate, gateway_port, gateway_filename,gateway_timeout)
    #run_controller(device_manager, node_params["experiment_time_sec"], controller_filename)
    run_experiment (device_manager, node_params["experiment_time_sec"], controller_filename, gateway_port, gateway_filename, gateway_timeout, gateway_baudrate)
    
    # add experiment in logbook datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    expt_params = {
        "date_time_str": current_time.strftime("%Y-%m-%d %H:%M:%S"),
        "expt_name": "Experiment 1",
        "expt_version": 1.0,
        "experiment_time_sec": node_params['experiment_time_sec'],
        "controller_filename": controller_filename,
        "gateway_filename": gateway_filename,
        "metadata_filename": None,
        "logbook_message": "LoRa hardware experiments"
    }
    logbook_add_entry(logbook_filename, expt_params)

# starts from here
if __name__ == "__main__":
    main()