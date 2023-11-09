import numpy as np
import pandas as pd
import struct
import matplotlib.pyplot as plt
from tabulate import tabulate
import pdb
import math

import logging

logger = logging.getLogger(__name__)


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

    packet_trace = packet_trace[packet_trace["RSSI"] > -50]

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


def extract_required_metrics_from_trace(
    gateway_df: pd.DataFrame, controller_df: pd.DataFrame
):
    # Extract only required metrics - node index, snr, rssi, packet_counter
    required_columns = ["NodeAddress", "Counter", "SNR", "RSSI"]
    gateway_extracted_df = gateway_df[required_columns]

    # merge gateway and controller dataframe as node metrics
    node_metrics_df = gateway_extracted_df.merge(
        controller_df, on="NodeAddress", how="left"
    )

    # filter nodes that didn't tranmitted any packets
    node_metrics_df = node_metrics_df.dropna(subset=["TransmittedPackets"])

    # filter rows where packete counter > tranmitted packets
    node_metrics_df = node_metrics_df[
        node_metrics_df["Counter"] <= node_metrics_df["TransmittedPackets"]
    ]

    return node_metrics_df


def compute_node_metrics(
    dataframe: pd.DataFrame,
    total_experiment_time: int,
    packet_airtime_sec: float,
    packet_size_bytes: int,
    offered_load_percent: float,
    desired_node_indices=None,
):
    # if no argument is given, read from all nodes
    if desired_node_indices is None:
        desired_node_indices = dataframe["NodeAddress"].unique()
    # if passing a single node index convert it into a list
    elif not isinstance(desired_node_indices, list):
        desired_node_indices = [desired_node_indices]

    # extracted metrics
    dataframe = dataframe[
        dataframe["NodeAddress"].isin(desired_node_indices)
    ]  # desired node_indices must be a list
    received_packets = dataframe.shape[0]
    snr_values = dataframe["SNR"].tolist()
    rssi_values = dataframe["RSSI"].tolist()
    total_transmitted_packets = sum(dataframe["TransmittedPackets"].unique())

    if total_transmitted_packets == 0:
        print(f"No transmitted packets with node_indices: {desired_node_indices}")
        return {}

    # computed metrics
    missing_packets = total_transmitted_packets - received_packets
    packet_reception_ratio = 1 - (missing_packets / total_transmitted_packets)
    packet_bits = packet_size_bytes * 8
    throughput = received_packets * packet_bits / total_experiment_time
    network_capacity = packet_bits / packet_airtime_sec
    normalized_throughput = throughput / network_capacity

    offered_load_bps = network_capacity * offered_load_percent / 100
    normalized_offered_load = offered_load_percent / 100

    node_metrics_dict = {}
    if len(desired_node_indices) == 1:
        node_metrics_dict["node_indices"] = desired_node_indices[0]
    node_metrics_dict["total_packets"] = total_transmitted_packets
    node_metrics_dict["missing_packets"] = missing_packets
    node_metrics_dict["packet_reception_ratio"] = packet_reception_ratio
    node_metrics_dict["offered_load_bps"] = offered_load_bps
    node_metrics_dict["throughput_bps"] = throughput
    node_metrics_dict["network_capacity_bps"] = network_capacity
    node_metrics_dict["normalized_throughput"] = normalized_throughput
    node_metrics_dict["normalized_offered_load"] = normalized_offered_load
    node_metrics_dict["snr_values"] = snr_values
    node_metrics_dict["rssi_values"] = rssi_values
    return node_metrics_dict


def compute_experiment_results(
    node_metrics_df: pd.DataFrame,
    experiment_time_sec: float,
    packet_airtime_sec: float,
    packet_size_bytes: int,
    offered_load_percent: float,
    **kwargs,
):
    desired_node_indices = node_metrics_df["NodeAddress"].unique()
    num_nodes = len(desired_node_indices)
    per_node_offered_load_percent = offered_load_percent / num_nodes

    expt_results_df = pd.DataFrame()
    for node_ind in desired_node_indices:
        desired_node_metrics_dict = compute_node_metrics(
            node_metrics_df,
            experiment_time_sec,
            packet_airtime_sec,
            packet_size_bytes,
            per_node_offered_load_percent,
            node_ind,
        )
        expt_results_df = expt_results_df._append(
            desired_node_metrics_dict, ignore_index=True
        )

    expt_results_df["snr_mean"] = expt_results_df["snr_values"].apply(
        lambda x: np.mean(np.asarray(x, dtype=np.float32))
    )

    return expt_results_df
