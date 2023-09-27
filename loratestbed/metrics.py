import numpy as np
import pandas as pd
import struct
import matplotlib.pyplot as plt
from tabulate import tabulate


def parse_byte_string(data):
    # unpack data from the byte string
    address, counter0, counter1, counter2 = struct.unpack("BBBB", data)

    # construct the counter from its bytes
    packet_counter = (counter2 << 16) | (counter1 << 8) | counter0

    return address, packet_counter


def filter_packet_trace(packet_trace: pd.DataFrame):
    # Remove packets with CRCStatus not zero
    packet_trace = packet_trace[packet_trace["CRCStatus"] == 0]

    # Remove packets with negative NodeAddress
    packet_trace = packet_trace[packet_trace["NodeAddress"] > 23]
    packet_trace = packet_trace[packet_trace["NodeAddress"] < 45]

    # Remove packets where all bytes of payload are zero
    packet_trace = packet_trace[
        packet_trace["Payload"].apply(lambda x: all(byte == 0 for byte in x[4:]))
    ]

    return packet_trace


def read_packet_trace(filename: str):
    column_names = ["Payload", "RSSI", "SNR", "CRCStatus"]

    packet_trace = pd.read_csv(filename, names=column_names)
    packet_trace["Payload"] = packet_trace["Payload"].apply(
        lambda x: bytes.fromhex(x if len(x) % 2 == 0 else "0" + x)
    )

    packet_trace["NodeAddress"], packet_trace["Counter"] = zip(
        *packet_trace["Payload"].apply(lambda x: parse_byte_string(x[:4]))
    )

    packet_trace = filter_packet_trace(packet_trace)

    return packet_trace


def metrics_from_trace(
    packet_trace: pd.DataFrame, node_packet_counts: dict[int] = None
):
    metrics_result = {}

    for name, group in packet_trace.groupby("NodeAddress"):
        # Extract vectors
        snr_vector = group["SNR"].values
        rssi_vector = group["RSSI"].values

        # Extract and sort the Counter vector
        counter_vector = group["Counter"].values
        if node_packet_counts is not None and name in node_packet_counts:
            counter_vector.append(node_packet_counts[name] + 1)

        sorted_counter = sorted(counter_vector)

        # Find missing packets by computing the difference between consecutive values
        differences = [
            sorted_counter[i + 1] - sorted_counter[i]
            for i in range(len(sorted_counter) - 1)
        ]

        missing_packets = sum(diff - 1 for diff in differences if diff > 1) - 1

        # Compute summary statistics for SNR and RSSI
        snr_stats = {
            "mean": snr_vector.mean(),
            "std": snr_vector.std(),
            "min": snr_vector.min(),
            "max": snr_vector.max(),
            "percentiles": {
                "25th": pd.Series(snr_vector).quantile(0.25),
                "50th": pd.Series(snr_vector).quantile(0.50),
                "75th": pd.Series(snr_vector).quantile(0.75),
            },
        }

        rssi_stats = {
            "mean": rssi_vector.mean(),
            "std": rssi_vector.std(),
            "min": rssi_vector.min(),
            "max": rssi_vector.max(),
            "percentiles": {
                "25th": pd.Series(rssi_vector).quantile(0.25),
                "50th": pd.Series(rssi_vector).quantile(0.50),
                "75th": pd.Series(rssi_vector).quantile(0.75),
            },
        }

        metrics_result[name] = {
            "SNR": snr_stats,
            "RSSI": rssi_stats,
            "Counter": sorted_counter,
            "MissingPackets": missing_packets,
        }

    return metrics_result


## Printers


def print_node_statistics(node_data):
    headers = ["Metric", "Value"]

    snr_data = [
        ["SNR Mean", node_data["SNR"]["mean"]],
        ["SNR Std", node_data["SNR"]["std"]],
        ["SNR Min", node_data["SNR"]["min"]],
        ["SNR Max", node_data["SNR"]["max"]],
        ["SNR 25th Percentile", node_data["SNR"]["percentiles"]["25th"]],
        ["SNR 50th Percentile", node_data["SNR"]["percentiles"]["50th"]],
        ["SNR 75th Percentile", node_data["SNR"]["percentiles"]["75th"]],
    ]

    rssi_data = [
        ["RSSI Mean", node_data["RSSI"]["mean"]],
        ["RSSI Std", node_data["RSSI"]["std"]],
        ["RSSI Min", node_data["RSSI"]["min"]],
        ["RSSI Max", node_data["RSSI"]["max"]],
        ["RSSI 25th Percentile", node_data["RSSI"]["percentiles"]["25th"]],
        ["RSSI 50th Percentile", node_data["RSSI"]["percentiles"]["50th"]],
        ["RSSI 75th Percentile", node_data["RSSI"]["percentiles"]["75th"]],
    ]

    print("=== SNR Statistics ===")
    print(tabulate(snr_data, headers=headers))
    print("\n=== RSSI Statistics ===")
    print(tabulate(rssi_data, headers=headers))
    print(f"\nMissing Packets: {node_data['MissingPackets']}\n")
    print("-" * 40)


def print_statistics(result):
    for node, data in result.items():
        print(f"Node Address: {node}\n")
        print_node_statistics(data)
