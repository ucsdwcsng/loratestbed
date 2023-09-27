from loratestbed.metrics import read_packet_trace

# import numpy as np
# import pandas as pd
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def test_read_packet_trace():
    filename: str = "./data/test_packet_trace.csv"
    packet_trace = read_packet_trace(filename)

    print(packet_trace)
