from loratestbed.metrics import read_packet_trace, metrics_from_trace, print_statistics
import os
import logging
import pdb
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
stdout_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
stdout_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(stdout_handler)

FULLPATH = "/".join(os.path.abspath(__file__).split("/")[:-1])
FULL_PATH_FILENAME: str = FULLPATH + "/data/test_packet_trace.csv"


def test_read_packet_trace():
    packet_trace = read_packet_trace(FULL_PATH_FILENAME)

    print(packet_trace)


def test_metrics():
    packet_trace = read_packet_trace(FULL_PATH_FILENAME)

    missing_pack_dict = {25: 30, 26: 14, 28: 18, 29: 15, 32: 44, 34: 16}

    total_pack_dict = {25: 60, 26: 60, 28: 60, 29: 60, 32: 60, 34: 60}

    metrics = metrics_from_trace(packet_trace, total_pack_dict)
    print()
    print(f"Node ID  | Missing")
    for node_id in metrics:
        missing_packets = metrics[node_id]["MissingPackets"]
        print(f"{node_id}  | {missing_packets}")
        assert missing_packets == missing_pack_dict[node_id]
