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


def main():
    gateway_trace_filename: str = "/tmp/gateway.csv"

    p1 = multiprocessing.Process(
        target=run_gateway,
        args=(
            2000000,
            "/dev/ttyACM0",
            gateway_trace_filename,
        ),
    )
    p1.start()

    result_matrix, config = run_controller("/dev/ttyACM1", "./configs/example.yaml")

    p1.terminate()

    device_list = config["device_list"]
    packets_per_device = {}
    for id, device_id in enumerate(device_list):
        packets_per_device[device_id] = result_matrix[id, 0]

    packet_trace = read_packet_trace(gateway_trace_filename)

    metrics = metrics_from_trace(packet_trace, packet_trace)
    print()
    print(f"Node ID  | % Success")
    for node_id in metrics:
        missing_packets = metrics[node_id]["MissingPackets"] + 1
        actual_packets = packets_per_device[node_id]
        print(f"Missing {missing_packets}")
        print(f"{node_id}  | {(actual_packets-missing_packets)/actual_packets*100:.1f}")


if __name__ == "__main__":
    main()
