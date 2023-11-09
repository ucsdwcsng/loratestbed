import pandas as pd
from datetime import datetime


def logbook_add_entry(logbook_file, expt_params):
    # Load the existing logbook if it exists, or create a new empty logbook
    try:
        logbook = pd.read_csv(logbook_file)
    except Exception as exception_message:
        print(f"Warning: {exception_message}, Initializing empty logbook...")
        logbook = pd.DataFrame()

    # Create a new entry as a DataFrame row
    new_entry = pd.DataFrame(
        {
            "timestamp": [expt_params["date_time_str"]],
            "expt_name": [expt_params["expt_name"]],
            "expt_version": [expt_params["expt_version"]],
            "experiment_time_sec": [expt_params["experiment_time_sec"]],
            "controller_filename": [expt_params["controller_filename"]],
            "gateway_filename": [expt_params["gateway_filename"]],
            "metadata_filename": [expt_params["metadata_filename"]],
            "comment": [expt_params["logbook_message"]],
        }
    )

    # Append the new entry to the logbook
    logbook = logbook._append(new_entry, ignore_index=True)

    # Write the updated logbook to the CSV file
    logbook.to_csv(logbook_file, index=False)


def logbook_load_entry(logbook_file, entry_index):
    # Load the logbook from the CSV file
    try:
        logbook = pd.read_csv(logbook_file)
    except Exception as exception_message:
        print(
            f"Error: {exception_message} \nPlease provide correct filename with full path"
        )
        return

    # Get the specified entry
    if entry_index >= 0:
        requested_entry = logbook.iloc[entry_index]
    else:
        requested_entry = logbook.iloc[entry_index]

    requested_entry = requested_entry.to_dict()
    return requested_entry, logbook


if __name__ == "__main__":
    # Example data for the logbook entry
    folder_name = "data_files_local"
    logbook_file = f"{folder_name}/experiment_logbook_local.csv"
    current_time = datetime.now()
    expt_params = {
        "date_time_str": current_time.strftime("%Y-%m-%d %H:%M:%S"),
        "expt_name": "Experiment 1",
        "expt_version": 1.0,
        "experiment_time_sec": 30.0,
        "controller_filename": f"controller_{current_time.strftime('%Y_%m_%d_%H_%M_%S')}",
        "gateway_filename": f"gateway_{current_time.strftime('%Y_%m_%d_%H_%M_%S')}",
        "metadata_filename": f"metadata_{current_time.strftime('%Y_%m_%d_%H_%M_%S')}",
        "logbook_message": "This is an example entry.",
    }

    # Calling the logbook_add_entry function to add the entry to the logbook
    for i in range(0, 3):
        expt_index = 10
        expt_params["expt_version"] = expt_index + i / 10
        logbook_add_entry(logbook_file, expt_params)

    # Calling the logbook_load_entry function to request an entry of the logbook
    for i in range(1, 5):
        loaded_entry, _ = logbook_load_entry(logbook_file, -i)
        print(loaded_entry)
