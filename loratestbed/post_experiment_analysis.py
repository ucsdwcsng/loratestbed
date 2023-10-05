import pandas as pd
import matplotlib.pyplot as plt
import logging
import argparse
import pdb

from loratestbed.metrics import read_packet_trace, extract_required_metrics_from_trace, compute_node_metrics
from loratestbed.experiment_logbook import logbook_load_entry

def make_parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("-f1", "--controller_filename", type=str, default=None, help="Filename to read controller saved data")
    ap.add_argument("-f2", "--gateway_filename", type=str, default=None, help="Filename to read controller saved data")
    ap.add_argument("-f", "--logbook_filename", type=str, default=None, help="Experiment logbook filename to get controller and gateway filenames and other details")

    return ap

def capture_metrics(gateway_output_file: str, controller_output_file: str):    
    # reading gateway output file
    packets_trace_from_gateway = read_packet_trace(gateway_output_file)

    # reading cpontroller output file
    column_names = ["NodeAddress","TransmittedPackets", "BackoffCounter","LBTCounter"]
    controller_metrics_dict = pd.read_csv(controller_output_file, header=None, names=column_names, index_col=False)

    # get combined node_metrics
    node_metrics_dataframe = extract_required_metrics_from_trace(packets_trace_from_gateway, controller_metrics_dict)

    return node_metrics_dataframe

def compute_experiment_results(node_metrics_df: pd.DataFrame, total_experiment_time: int):
    desired_node_indices = node_metrics_df['NodeAddress'].unique()

    node_metrics_dict = compute_node_metrics(node_metrics_df, total_experiment_time, desired_node_indices)
    print("------------Computed node metrics (all nodes) -------------")
    for key, value in node_metrics_dict.items():
        print(f"{key}: {value}")

    expt_results_df = pd.DataFrame()
    for node_ind in desired_node_indices:
        desired_node_metrics_dict = compute_node_metrics(node_metrics_df, total_experiment_time, [node_ind])
        expt_results_df = expt_results_df._append(desired_node_metrics_dict, ignore_index=True)
        print(f"------------Computed node metrics for node: {node_ind} -------------")
        for key, value in desired_node_metrics_dict.items():
            print(f"{key}: {value}")
    
    print("------------ Results table (summary)-------------")
    combined_results_df = expt_results_df._append(node_metrics_dict, ignore_index=True)
    print_columns = ['node_indices', 'total_packets', 'missing_packets', 'packet_reception_ratio', 'normalized_throughput','normalized_offered_load']
    print (combined_results_df[print_columns])
    print (f"NaN in above table refer to all nodes")
    return expt_results_df

def generate_plots(experiment_results_df: pd.DataFrame):
    snr_array_list = experiment_results_df['snr_values'].to_list()

    for snr_array in snr_array_list:
        plt.plot(snr_array)
    plt.title('SNR array values')
    plt.show()

# main function
def main():
    logging.basicConfig(
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    parser = make_parser()
    args = parser.parse_args()
    
    if (args.controller_filename is not None) and (args.gateway_filename is not None):
        controller_output_file = args.controller_filename
        gateway_output_file = args.gateway_filename
    elif (args.logbook_filename is not None):
        loaded_entry, _ = logbook_load_entry(args.logbook_filename, -1)
        controller_output_file = loaded_entry['controller_filename']
        gateway_output_file = loaded_entry['gateway_filename']
        print(f"controller file: {controller_output_file}, \ngateway file:{gateway_output_file}")
    else:
        folder_name = "tests/data/"
        controller_output_file = f"{folder_name}/contoller_test.csv"
        gateway_output_file = f"{folder_name}/gateway_test.csv"

    # get combined node metrics from gateway and controller
    node_metrics_df = capture_metrics(gateway_output_file, controller_output_file)

    # compute experiment results
    total_experiment_time = 30 
    expt_results_df = compute_experiment_results(node_metrics_df, total_experiment_time)

    generate_plots(expt_results_df)

# starts from here
if __name__ == "__main__":
    main()