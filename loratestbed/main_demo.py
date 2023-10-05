import argparse
import logging
import pdb
import time
import yaml
import multiprocessing


from loratestbed.main_controller import run_controller
from loratestbed.main_gateway import run_gateway
from loratestbed.metrics import read_packet_trace, metrics_from_trace

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
    metrics = metrics_from_trace(packet_trace, packet_trace)


if __name__ == "__main__":
    main()
