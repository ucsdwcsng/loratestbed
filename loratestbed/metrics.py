import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def read_packet_trace(filename: str):
    column_names = ["Payload", "SNR", "NodeAddress", "CRCStatus"]

    packet_trace = pd.read_csv(filename, names=column_names)
    packet_trace["Payload"] = packet_trace["Payload"].apply(
        lambda x: bytes.fromhex(x if len(x) % 2 == 0 else "0" + x)
    )

    return packet_trace
