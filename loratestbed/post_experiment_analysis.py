import pandas as pd
import matplotlib.pyplot as plt
import logging
import pdb

from loratestbed.metrics import read_packet_trace, extract_required_metrics_from_trace, compute_node_metrics


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
        desired_node_metrics_dict = compute_node_metrics(node_metrics_df, total_experiment_time, node_ind)
        expt_results_df = expt_results_df._append(desired_node_metrics_dict, ignore_index=True)
        print(f"------------Computed node metrics for node: {node_ind} -------------")
        for key, value in desired_node_metrics_dict.items():
            print(f"{key}: {value}")
    
    print("------------ Results table -------------")
    print (expt_results_df)

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

    # variables
    folder_name = "tests/data/"
    gateway_output_file = f"{folder_name}/gateway_test.csv"
    controller_output_file = f"{folder_name}/contoller_test.csv"

    # get combined node metrics from gateway and controller
    node_metrics_df = capture_metrics(gateway_output_file, controller_output_file)

    # compute experiment results
    total_experiment_time = 30 
    expt_results_df = compute_experiment_results(node_metrics_df, total_experiment_time)

    generate_plots(expt_results_df)

# starts from here
if __name__ == "__main__":
    main()