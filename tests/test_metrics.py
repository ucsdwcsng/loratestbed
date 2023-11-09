from loratestbed.metrics import read_packet_trace, extract_required_metrics_from_trace
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
