# loratestbed

An infrastructure-less, arduino-compatible LoRa testbed for PHY and MAC research.

## Run a simple experiment with 1 device (9/14/23)

```bash
poetry run python3 ./loratestbed/main_controller.py -p /dev/ttyACM0 
```

This code will run a 20 second experiment with only device no. 33 and retrieve the total number of transmitted packets.

## Setup and installation

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
