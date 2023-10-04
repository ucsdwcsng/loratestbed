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

    packet_trace = pd.read_csv(filename, names=column_names, index_col=False)
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
            counter_vector = np.append(counter_vector, node_packet_counts[name] + 1)

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

def extract_required_metrics_from_trace(gateway_df: pd.DataFrame, controller_df: pd.DataFrame):
    # Extract only required metrics - node index, snr, rssi, packet_counter
    required_columns = ['NodeAddress', 'Counter', 'SNR', 'RSSI']
    gateway_extracted_df = gateway_df[required_columns]

    # merge gateway and controller dataframe as node metrics
    node_metrics_df = gateway_extracted_df.merge(controller_df, on='NodeAddress', how='left')

    # filter nodes that didn't tranmitted any packets
    node_metrics_df = node_metrics_df.dropna(subset=['TransmittedPackets'])

    # filter rows where packete counter > tranmitted packets
    node_metrics_df = node_metrics_df[node_metrics_df['Counter'] <= node_metrics_df['TransmittedPackets']]

    return node_metrics_df

def compute_node_metrics(dataframe: pd.DataFrame, total_experiment_time: int, desired_node_indices = None):
    # if no argument is given, read from all nodes
    if desired_node_indices is None:
        desired_node_indices = dataframe['NodeAddress'].unique()
    # if passing a single node index convert it into a list
    elif not isinstance(desired_node_indices,list):
        desired_node_indices = [desired_node_indices]

    # extracted metrics
    dataframe = dataframe[dataframe['NodeAddress'].isin(desired_node_indices)] # desired node_indices must be a list
    received_packets = dataframe.shape[0]
    snr_values = dataframe['SNR'].tolist()
    rssi_values = dataframe['RSSI'].tolist()
    total_transmitted_packets = sum(dataframe['TransmittedPackets'].unique())

    if total_transmitted_packets == 0:
        print(f"No tranmitted packets with node_indices: {desired_node_indices}")
        return {}

    # known_values
    packet_duration = 0.126 # 126 ms
    packet_bytes = 16 # 16 bytes
    no_bits_in_byte = 8
    print(f"Assuming all nodes transmit known (same) packet length with duration {packet_duration*1000} ms and bytes {packet_bytes}")

    # computed metrics
    missing_packets = total_transmitted_packets - received_packets
    packet_reception_ratio = 1 - (missing_packets/total_transmitted_packets)
    packet_bits = packet_bytes*no_bits_in_byte
    throughput = received_packets*packet_bits/total_experiment_time
    network_capacity = packet_bits/packet_duration
    normalized_throughput = throughput/network_capacity
    offered_load = total_transmitted_packets*packet_bits/total_experiment_time
    normalized_offered_load = offered_load/network_capacity

    node_metrics_dict = {}
    if len(desired_node_indices) == 1:
        node_metrics_dict['node_indices'] = desired_node_indices[0]
    node_metrics_dict['total_packets'] = total_transmitted_packets
    node_metrics_dict['missing_packets'] = missing_packets 
    node_metrics_dict['packet_reception_ratio'] = packet_reception_ratio 
    node_metrics_dict['offered_load_bps'] = offered_load 
    node_metrics_dict['throughput_bps'] = throughput 
    node_metrics_dict['network_capacity_bps'] = network_capacity 
    node_metrics_dict['normalized_throughput'] = normalized_throughput 
    node_metrics_dict['normalized_offered_load'] = normalized_offered_load 
    node_metrics_dict['snr_values'] = snr_values 
    node_metrics_dict['rssi_values'] = rssi_values 
    return node_metrics_dict

def get_node_metrics_statistics(node_metric_list):
    node_stats = {
    "mean": node_metric_list.mean(),
    "std": node_metric_list.std(),
    "min": node_metric_list.min(),
    "max": node_metric_list.max(),
    "percentiles": {
        "25th": pd.Series(node_metric_list).quantile(0.25),
        "50th": pd.Series(node_metric_list).quantile(0.50),
        "75th": pd.Series(node_metric_list).quantile(0.75),
        },
    }
    return node_stats



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
