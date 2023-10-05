import argparse
import logging
import pdb
import time
import yaml

from loratestbed.controller import SerialInterface
from loratestbed.device_manager import DeviceManager
from loratestbed.main_gateway import run_gateway


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

    # %% post-experiment: pinging devices and get results
    logging.info("Pinging devices")
    pingable_devices = device_manager._ping_devices(config["device_list"])
    assert (
        pingable_devices == config["device_list"]
    ), "Not all devices responded to ping"

    logging.info("Reading all result registers")
    result_mat = device_manager.result_registers_from_device()
    for id, device_idx in enumerate(config["device_list"]):
        logging.info(f"Device {device_idx} sent {result_mat[id, 0]:.0f} packets")

    return result_mat, config


# starts from here
if __name__ == "__main__":
    main()
