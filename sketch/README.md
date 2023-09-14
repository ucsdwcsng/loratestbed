# Arduino Sketches for the LoRa testbed

## Setting up on the STM-32 based Nucleo Platform

### Arduino Core for STM32

Get the Arduino core for STM32 by following the instructions on [this link](https://github.com/stm32duino/Arduino_Core_STM32). After installing the core, make sure to verify that the board is set to the right value and programming is set to `MASS STORAGE` (click on tools).

### `arduino-lmic` library from WCSNG

Get the modified `arduino-lmic` library from [github.com/ucsdwcsng/arduino-lmic](https://github.com/ucsdwcsng/arduino-lmic). This library contains the LoRa driver with all the hooks required for the testbed. The driver also implements various MAC protocols and packet schedulers. This library has to be moved to arduino's default `Library` folder.

## The three sketches and how to flash them

1. `device`: This sketch contains the code for a device. Make sure to modify the `#define NODE_IDX 40` line and replace `40` with a node index between `24-44`. This is the only way to differentiate between two different devices.
2. `controller`: The central controller of the testbed. Can be flashed as-is.
3. `gateway_reference`: A reference implementation of a LoRa gateway using a LoRa IoT device. This implementation can be used to verify decoding if a gateway under test is not available.

## FAQs

1. How do I know if things are working?
    - Check serial monitor
    - Consider using the debug sketches in the debugging folder
