import serial
import matplotlib.pyplot as plt
from drawnow import *
import atexit
import argparse
import sys

import numpy.core._methods
import numpy.lib.format



parser = argparse.ArgumentParser(description='plot some data from serial port')
parser.add_argument('port', type=str, help='specify serial port (i.e: "COM5")')
parser.add_argument('-b', '--baudrate', type=int, default=38400, help='default: 38400')
parser.add_argument('-pr', '--protocol', type=str, default="8N1", help='default: "8N1"')
parser.epilog = 'have fun...'

args = parser.parse_args()


ser = serial.Serial(port = args.port, baudrate = args.baudrate)

if args.protocol == '7E1':
    ser.bytesize=7
    ser.parity='E'
    ser.stopbits=1

values = []

plt.ion()


def plotValues():
    plt.title('...')
    plt.grid(True)
    plt.ylabel('Values')
    plt.plot(values, 'rx-')
    plt.legend(loc='upper right')


print('for help use option "--help"')
print('quit with ctrl-c')
    
while True:
    value = ser.readline().decode("utf-8")
    try:
        val_f = float(value)
        values.append(val_f)
    except ValueError:
        if '$' in value:
            drawnow(plotValues)
            values = []
        else:
            print("error! cannot cast %s" %value.hex())
    

    