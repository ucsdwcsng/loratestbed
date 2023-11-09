import argparse
import logging
import pdb
import time
import yaml
import multiprocessing
import os
import datetime
import shutil

from loratestbed.main_controller import run_controller
from loratestbed.main_gateway import run_gateway
from loratestbed.metrics import (
    read_packet_trace,
    extract_required_metrics_from_trace,
    compute_experiment_results,
    generate_plots,
)
from loratestbed.experiment_logbook import logbook_add_entry

logging.basicConfig(
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)


def make_parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("-g", "--gateway", required=True, help="Gateway Port Name")
    ap.add_argument("-c", "--controller", required=True, help="Controller Port Name")
    ap.add_argument(
        "--config", required=True, help="Path to the YAML configuration file"
    )
    # Add experiment name and comment as two different arguments
    ap.add_argument(
        "--experiment_name",
        default="Experiment 1",
        help="Experiment Name",
    )
    ap.add_argument(
        "--logbook_message",
        default="LoRa hardware experiments",
        help="Message for logbook",
    )
    return ap


def run_testbed(
    gateway_port: str,
    controller_port: str,
    config_filename: str,
    experiment_name: str = "",
    logbook_message: str = "",
):
    gateway_trace_filename: str = "/tmp/gateway.csv"

    p1 = multiprocessing.Process(
        target=run_gateway,
        args=(
            2000000,
            gateway_port,
            gateway_trace_filename,
        ),
    )
    p1.start()

    result_df, config = run_controller(controller_port, config_filename)

    p1.terminate()

    packet_trace = read_packet_trace(gateway_trace_filename)
    node_metrics_dataframe = extract_required_metrics_from_trace(
        packet_trace, result_df
    )
    expt_results_df = compute_experiment_results(node_metrics_dataframe, **config)

    total_offered_load = expt_results_df.normalized_offered_load.sum()
    total_normalized_throughput = expt_results_df.normalized_throughput.sum()
    network_capacity_bps = expt_results_df.network_capacity_bps.iloc[0]

    # print network statistics:
    logging.info(f"Network Capacity: {network_capacity_bps:.2f} bps")
    logging.info(
        f"Total Offered Load: {total_offered_load*100:.2f}% ({network_capacity_bps*total_offered_load:.2f} bps)"
    )
    logging.info(
        f"Total Normalized Throughput: {total_normalized_throughput*100:.2f}% ({network_capacity_bps*total_normalized_throughput:.2f} bps)"
    )
    logging.info(
        expt_results_df[
            [
                "node_indices",
                "total_packets",
                "packet_reception_ratio",
                "throughput_bps",
                "normalized_throughput",
                "normalized_offered_load",
            ]
        ]
    )

    # First code: Saving results and config files
    current_time = time.strftime("%Y%m%d-%H%M%S")
    results_folder = "./results"
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)
    results_filename = f"{results_folder}/results-{current_time}.pkl"
    expt_results_df.to_pickle(results_filename)
    config_filename = f"{results_folder}/config-{current_time}.yaml"
    with open(config_filename, "w") as f:
        yaml.dump(config, f)
    logging.info(f"Saved results to {results_filename}, configs to {config_filename}")
    gateway_filename = f"{results_folder}/gateway-{current_time}.csv"
    # copy gateway_trace_filename to gateway_filename
    shutil.copy(gateway_trace_filename, gateway_filename)

    # Second code: Logbook functionality
    logbook_filename = f"{results_folder}/experiment_logbook.csv"

    # Update the experiment parameters to include filenames of results and config
    expt_params = {
        "date_time_str": current_time,
        "expt_name": experiment_name,
        "expt_version": 1.0,
        "experiment_time_sec": config["experiment_time_sec"],
        "controller_filename": results_filename,  # Updated to include the results filename
        "gateway_filename": gateway_filename,  # Assuming there's no gateway file in the first code snippet
        "metadata_filename": config_filename,  # Updated to include the config filename
        "logbook_message": logbook_message,
    }
    logbook_add_entry(logbook_filename, expt_params)


def main():
    parser = make_parser()
    args = parser.parse_args()

    run_testbed(
        args.gateway,
        args.controller,
        args.config,
        args.experiment_name,
        args.logbook_message,
    )


if __name__ == "__main__":
    main()
