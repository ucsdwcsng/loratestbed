import argparse
import logging
import pdb
import time
import yaml
import multiprocessing


from loratestbed.main_controller import run_controller
from loratestbed.main_gateway import run_gateway
from loratestbed.metrics import (
    read_packet_trace,
    extract_required_metrics_from_trace,
    compute_experiment_results,
    generate_plots,
)
import logging

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
    return ap


def main():
    parser = make_parser()
    args = parser.parse_args()

    gateway_trace_filename: str = "/tmp/gateway.csv"

    p1 = multiprocessing.Process(
        target=run_gateway,
        args=(
            2000000,
            args.gateway,
            gateway_trace_filename,
        ),
    )
    p1.start()

    result_df, config = run_controller(args.controller, args.config)

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
    print(f"Network Capacity: {network_capacity_bps:.2f} bps")
    print(
        f"Total Offered Load: {total_offered_load*100:.2f}% ({network_capacity_bps*total_offered_load:.2f} bps)"
    )
    print(
        f"Total Normalized Throughput: {total_normalized_throughput*100:.2f}% ({network_capacity_bps*total_normalized_throughput:.2f} bps)"
    )
    print(
        expt_results_df[
            [
                "node_indices",
                "total_packets",
                "packet_reception_ratio",
                "throughput_bps",
            ]
        ]
    )


if __name__ == "__main__":
    main()
