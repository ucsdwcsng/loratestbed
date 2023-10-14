# LoRa Testbed

An infrastructure-less, arduino-compatible LoRa testbed for PHY and MAC research. The user will simply provide a config file (that contains the experiment configuration details) to the testbed. The controller will communicate with the network to then return the results after the experiment has ended. See below for a high level overview.

![]('./../docs/testbed_setup_diagram.png)
*Diagram 1: High level overview of the LoRa Testbed.*

## Run a simple experiment with an example configuration

```bash
poetry run python3 ./loratestbed/run_testbed.py -g /dev/ttyACM0 -c /dev/ttyACM1 --config ./configs/example.yaml
```

You will need to have device ID 33 and 26 active to run this successfully.

### Configuration format

The configuration YAML file should necessarily have the following format/fields:

```yaml
device_list: [33, 26] # List of device IDs
experiment_time_sec: 10 # Experiment time in seconds
transmit_interval_msec: 200 # Average time interval between consecutive transmissions from each device
packet_size_bytes: 16
mac_protocol: "csma" # MAC protocol used by the devices
packet_arrival_model: "poisson" # Packet generation model used by the devices.
# PHY layer parameters
transmit_SF: "SF8" # Spreading factor
receive_SF: "SF8"
transmit_BW: "BW125" # Bandwidth: "BW125", "BW250", "BW500
receive_BW: "BW125"
transmit_CR: "CR_4_8" # Code rate
receive_CR: "CR_4_8"
```

## Setup and installation

### Setting up the testbed

[Click here](./sketch/README.md) to go to the documentation on flashing various components in the testbed and bringing them up.

### Host software

Install poetry

```bash
pip install -U poetry
```

Navigate to the root directory of this git repository. Run tests:

```bash
poetry run pytest
```

Install:

```bash
poetry install
```
