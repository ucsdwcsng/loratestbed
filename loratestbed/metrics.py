import numpy as np
import pandas as pd
import struct
import matplotlib.pyplot as plt
from tabulate import tabulate
import pdb
import math

import logging

logger = logging.getLogger(__name__)


def comp_lora_airtime(PL, SF, CRC, IH, DE, CR, SR, NS):
    """
    Compute Airtime of LoRa
    PL: number of payload bytes
    SF: spreading factor
    CRC: presence of a CRC (0 if absent, 1 if present)
    IH: whether the header is enabled (0 if enabled, 1 if disabled)
    DE: whether low data rate optimization is on (0 if disabled, 1 if enabled)
    CR: the coding rate (1 meaning 4/5 rate, 4 meaning 4/8 rate)
    SR: Sampling Rate
    NS: Number of samples per chirp at sample rate
    """
    max_inp_1 = math.ceil(
        (8 * PL - 4 * SF + 28 + 16 * CRC - 20 * IH) / (4 * (SF - 2 * DE))
    ) * (CR + 4)
    max_inp_2 = 0
    max_val = max(max_inp_1, max_inp_2)

    n_pb = 8 + max_val

    air_time = NS * (n_pb + 12.25) / SR

    return air_time


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
        # TODO: is there a +1 here?

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
    dataframe: pd.DataFrame, total_experiment_time: int, desired_node_indices=None
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

    # known_values
    packet_duration = 0.126  # 126 ms
    packet_bytes = 16  # 16 bytes
    no_bits_in_byte = 8
    logger.warning(
        f"Using hard-coded values for packet duration: {packet_duration}, packet bytes {packet_bytes}"
    )
    # print(
    #     f"Assuming all nodes transmit known (same) packet length with duration {packet_duration*1000} ms and bytes {packet_bytes}"
    # )

    # computed metrics
    missing_packets = total_transmitted_packets - received_packets
    packet_reception_ratio = 1 - (missing_packets / total_transmitted_packets)
    packet_bits = packet_bytes * no_bits_in_byte
    throughput = received_packets * packet_bits / total_experiment_time
    network_capacity = packet_bits / packet_duration
    normalized_throughput = throughput / network_capacity
    offered_load = total_transmitted_packets * packet_bits / total_experiment_time
    normalized_offered_load = offered_load / network_capacity

    node_metrics_dict = {}
    if len(desired_node_indices) == 1:
        node_metrics_dict["node_indices"] = desired_node_indices[0]
    node_metrics_dict["total_packets"] = total_transmitted_packets
    node_metrics_dict["missing_packets"] = missing_packets
    node_metrics_dict["packet_reception_ratio"] = packet_reception_ratio
    node_metrics_dict["offered_load_bps"] = offered_load
    node_metrics_dict["throughput_bps"] = throughput
    node_metrics_dict["network_capacity_bps"] = network_capacity
    node_metrics_dict["normalized_throughput"] = normalized_throughput
    node_metrics_dict["normalized_offered_load"] = normalized_offered_load
    node_metrics_dict["snr_values"] = snr_values
    node_metrics_dict["rssi_values"] = rssi_values
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


def compute_experiment_results(
    node_metrics_df: pd.DataFrame, experiment_time_sec: float, **kwargs
):
    desired_node_indices = node_metrics_df["NodeAddress"].unique()

    # node_metrics_dict = compute_node_metrics(
    #     node_metrics_df, total_experiment_time, desired_node_indices
    # )
    # print("------------Computed node metrics (all nodes) -------------")
    # for key, value in node_metrics_dict.items():
    #     print(f"{key}: {value}")

    expt_results_df = pd.DataFrame()
    for node_ind in desired_node_indices:
        desired_node_metrics_dict = compute_node_metrics(
            node_metrics_df, experiment_time_sec, node_ind
        )
        expt_results_df = expt_results_df._append(
            desired_node_metrics_dict, ignore_index=True
        )
        # print(f"------------Computed node metrics for node: {node_ind} -------------")
        # for key, value in desired_node_metrics_dict.items():
        #     print(f"{key}: {value}")

    # print("------------ Results table -------------")
    # print(expt_results_df)

    expt_results_df["snr_mean"] = expt_results_df["snr_values"].apply(
        lambda x: np.mean(np.asarray(x, dtype=np.float32))
    )

    return expt_results_df
