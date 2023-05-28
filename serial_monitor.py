# Serial Monitor in terminal with Python taken from 
# https://uclalemur.com/blog/python-script-to-read-serial-monitor

# pySerial docs: https://pyserial.readthedocs.io/en/latest/

import serial 
import argparse

def print_serial(name):
    try:
        serial_port = serial.Serial(name,115200)
        print(f"The Port name is {serial_port.name}")
        while True:
            lines = serial_port.readline()
            print(lines)
    except:
        print("ERROR")
        print("check port")
        exit() 

ap = argparse.ArgumentParser()
ap.add_argument("-p","--port",required = True, help = "Enter Port Name")
args = vars(ap.parse_args())

PORT = args['port']

print_serial(PORT) 