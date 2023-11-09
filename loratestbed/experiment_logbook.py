import pandas as pd
from datetime import datetime


def logbook_add_entry(logbook_file, expt_params):
    try:
        logbook = pd.read_csv(logbook_file)
    except Exception as exception_message:
        print(f"Warning: {exception_message}, Initializing empty logbook...")
        logbook = pd.DataFrame()

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

    logbook = logbook.append(new_entry, ignore_index=True)
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
