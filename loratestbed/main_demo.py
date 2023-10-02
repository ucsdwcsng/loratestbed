import argparse
import logging
import pdb
import time
import yaml
import multiprocessing


from loratestbed.main_controller import run_controller
from loratestbed.main_gateway import run_gateway
from loratestbed.metrics import read_packet_trace, metrics_from_trace


def main():
    gateway_trace_filename: str = "/tmp/gateway.csv"

    p1 = multiprocessing.Process(
        target=run_gateway,
        args=(
            2000000,
            "/dev/ttyACM1",
        ),
    )
    p1.start()

    result_matrix, config = run_controller("/dev/ttyACM0", "./configs/config.yaml")

    p1.terminate()

    device_list = config["device_list"]
    packets_per_device = {}
    for id, device_id in enumerate(device_list):
        packets_per_device[device_id] = result_matrix[id, 0]

    packet_trace = read_packet_trace("")

    metrics = metrics_from_trace(packet_trace, gateway_trace_filename)
    print()
    print(f"Node ID  | Missing")
    for node_id in metrics:
        missing_packets = metrics[node_id]["MissingPackets"]
        print(f"{node_id}  | {missing_packets}")


if __name__ == "__main__":
    main()
