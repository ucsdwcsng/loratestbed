import argparse
import logging
import pdb
import time
import yaml

from loratestbed.controller import SerialInterface
from loratestbed.device_manager import DeviceManager
from loratestbed.main_gateway import run_gateway
from loratestbed.experiment_logbook import logbook_add_entry


def make_parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--port", required=True, help="Enter Port Name")
    ap.add_argument(
        "-c", "--config", required=True, help="Path to the YAML configuration file"
    )
    return ap


def load_config(yaml_path):
    with open(yaml_path, "r") as f:
        config = yaml.safe_load(f)
    return config


# main function
def main():
    logging.basicConfig(
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = make_parser()
    args = parser.parse_args()

    # device_list = [26, 27, 28, 29, 33]
    # # device_list = [25, 26, 28, 29, 32, 33, 34]
    # interface = SerialInterface(args.controller_port)
    # logging.info("Setting up DeviceManager")
    # device_manager = DeviceManager(device_list, interface)
    # logging.info("Disabling all devices in range")
    # device_manager.disable_all_devices()# Disable all devices, later only set experiment time to the desired nodes

    # # updating MAC Params
    # logging.info("Updating MAC params")
    # device_manager.set_mac_protocol("ALOHA", 12, 64*12)

    # # initialzing node parameters
    # node_params = {
    #     "experiment_time_sec": 60,
    #     "transmit_interval_msec": 1000,
    #     "packet_arrival_model": "POISSON",  #("PERIODIC", "POISSON")
    #     "periodic_variance_x10_msec": 0,
    #     "transmit_SF": "SF8", "receive_SF": "SF8", #("SF7", "SF8" ... , "SF12, "FSK", SF_RFU")
    #     "transmit_BW": "BW125", "receive_BW": "BW125", #("BW125", "BW250", "BW500", BW_RFU")
    #     "transmit_CR": "CR_4_8", "receive_CR": "CR_4_8", #("CR_4_5", "CR_4_6", "CR_4_7", "CR_4_8")
    #     }

    # # updating parameters (comment params that are not required to change)
    # device_manager.update_node_params(
    #     EXPT_TIME = [node_params["experiment_time_sec"]],
    #     TX_INTERVAL = [node_params["transmit_interval_msec"]],
    #     ARRIVAL_MODEL = [node_params["packet_arrival_model"]],
    #     # ARRIVAL_MODEL=[node_params["packet_arrival_model"], node_params["periodic_variance_x10_msec"]],
    #     # LORA_SF=[node_params["transmit_SF"], node_params["receive_SF"]],
    #     LORA_BW=[node_params["transmit_BW"], node_params["receive_BW"]],
    #     # LORA_CR=[node_params["transmit_CR"], node_params["receive_CR"]],
    # )

    # # runnning experiment
    # folder_name = "data_files_local"
    # current_time = datetime.now()
    # controller_filename = f"{folder_name}/controller_{current_time.strftime('%Y_%m_%d_%H_%M_%S')}.csv"
    # logbook_filename = f"{folder_name}/experiment_logbook.csv"
    # gateway_filename = f"{folder_name}/gateway_{current_time.strftime('%Y_%m_%d_%H_%M_%S')}.csv"
    # gateway_port = args.gateway_port
    # gateway_baudrate = 2000000
    # gateway_timeout = node_params["experiment_time_sec"]+10

    # # run_gateway(gateway_baudrate, gateway_port, gateway_filename,gateway_timeout)
    # # run_controller(device_manager, node_params["experiment_time_sec"], controller_filename)
    # run_experiment (device_manager, node_params["experiment_time_sec"], controller_filename, gateway_port, gateway_filename, gateway_timeout, gateway_baudrate)

    # # add experiment in logbook datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    # expt_params = {
    #     "date_time_str": current_time.strftime("%Y-%m-%d %H:%M:%S"),
    #     "expt_name": "Experiment 1",
    #     "expt_version": 1.0,
    #     "experiment_time_sec": node_params['experiment_time_sec'],
    #     "controller_filename": controller_filename,
    #     "gateway_filename": gateway_filename,
    #     "metadata_filename": None,
    #     "logbook_message": "LoRa hardware experiments"
    # }
    # logbook_add_entry(logbook_filename, expt_params)
    run_controller(args.port, args.config)


def run_controller(port, config):
    config = load_config(config)

    interface = SerialInterface(port)
    logging.info("Setting up DeviceManager")
    device_manager = DeviceManager(config["device_list"], interface)

    # TODO: fix this
    # device_manager.update_node_params(
    #     EXPT_TIME=[experiment_time_sec],
    #     # TX_INTERVAL=[transmit_interval_msec],
    #     # ARRIVAL_MODEL=[packet_arrival_model],
    #     # ARRIVAL_MODEL=[packet_arrival_model, periodic_variance_x10_msec],
    #     # LORA_SF=[transmit_SF, receive_SF],
    #     LORA_BW=[transmit_BW, receive_BW],
    #     # LORA_CR=[transmit_CR, receive_CR],
    # )

    device_manager.disable_all_devices()

    # pre-experiment: updating parameters
    logging.info(f"Setting experiment time to {config['experiment_time_sec']} seconds")
    device_manager._set_experiment_time_seconds(config["experiment_time_sec"])

    # device_manager.update_node_params(**config)

    logging.info(
        f"Setting transmit interval time to {config['transmit_interval_msec']} milliseconds"
    )
    device_manager._set_transmit_interval_milliseconds(config["transmit_interval_msec"])

    logging.info(
        f"Setting scheduler transmit interval mode to {config['packet_arrival_model']}"
    )
    device_manager._set_packet_arrival_model(config["packet_arrival_model"])

    logging.info(
        f"Setting transmit SF to {config['transmit_SF']} and receive SF to {config['receive_SF']}"
    )
    device_manager._set_transmit_and_receive_SF(
        config["transmit_SF"], config["receive_SF"]
    )

    logging.info(
        f"Setting transmit BW to {config['transmit_BW']} and receive BW to {config['receive_BW']}"
    )
    device_manager._set_transmit_and_receive_BW(
        config["transmit_BW"], config["receive_BW"]
    )

    logging.info(
        f"Setting transmit CR to {config['transmit_CR']} and receive CR to {config['receive_CR']}"
    )
    device_manager._set_transmit_and_receive_CR(
        config["transmit_CR"], config["receive_CR"]
    )

    logging.info(f"Setting packet size to {config['packet_size_bytes']} bytes")
    device_manager.set_packet_size_bytes(config["packet_size_bytes"])

    logging.info(f"Setting MAC protocol to {config['mac_protocol']}")
    device_manager.set_mac_protocol(config["mac_protocol"])

    # %% running experiment
    logging.info("Triggering all devices")
    device_manager.trigger_all_devices()

    logging.info("Waiting for experiment to finish...")
    time.sleep(config["experiment_time_sec"] + 10)

    # post-experiment: pinging devices and get results
    logging.info("Pinging devices")
    pingable_devices = device_manager._ping_devices(config["device_list"])
    assert (
        pingable_devices == config["device_list"]
    ), "Not all devices responded to ping"

    logging.info("Reading all result registers")
    result_df = device_manager.results()

    logging.debug(f"{result_df}")

    return result_df, config


# starts from here
if __name__ == "__main__":
    main()
