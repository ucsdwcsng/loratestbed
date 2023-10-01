# Arduino Sketches for the LoRa testbed

## Setting up on the STM-32 based Nucleo Platform

### 1. Get Arduino Core for STM32

In your Arduino IDE, get the Arduino core for STM32 by following the instructions [here](https://github.com/stm32duino/Arduino_Core_STM32#getting-started). To install, you will need to go to "File" -> "Preferences" -> "Additional Boards Managers URLs" and then paste in this link: 

https://github.com/stm32duino/BoardManagerFiles/raw/main/package_stmicroelectronics_index.json. 

After installing the core and connecting a device, make sure to verify that the board is set to the right value and programming is set to `MASS STORAGE` (see "Tools").

### 2. Use `arduino-lmic` library from WCSNG

Get the modified `arduino-lmic` library from [github.com/ucsdwcsng/arduino-lmic](https://github.com/ucsdwcsng/arduino-lmic#installing). This library contains the LoRa driver with all the hooks required for the testbed. The driver also implements various MAC protocols and packet schedulers. 

The easiest method to install this library would be to download it as a `.zip` file. Then, in the Arduino IDE go to "Sketch" -> "Include Library" -> "Add .ZIP Library."

## How to flash devices with `.ino` code 

1. `device`: This sketch contains the code for a device. Make sure to modify the `#define NODE_IDX 40` line and replace `40` with a node index between `24-44`. This is the only way to differentiate between two different devices.
2. `controller`: The central controller of the testbed. Can be flashed as-is.
3. `gateway_reference`: A reference implementation of a LoRa gateway using a LoRa IoT device. This implementation can be used to verify decoding if a gateway under test is not available.

To install these sketches to a device, connect the required device to your computer and open in the Arduino IDE (which has been setup in the previous steps). Select the appropriate port in "Select Board" and then click "Upload." In this manner, all devices can be flashed with the appropriate sketches as needed. 

## FAQs

1. How do I know if things are working?
    - Check serial monitor for any outputs. 
    - Consider using the debug sketches in the debugging folder
      - `rx_debug` will program the device to always receive while `tx_debug` will program the device to always transmit. This can be used to troubleshoot any issues that may arise. 
