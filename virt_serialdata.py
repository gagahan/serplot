import serial
import time
import numpy as np
import matplotlib.pylab as plt
from serial.serialutil import SerialException


sep = ','
end = '$'


ser = serial.Serial('/dev/tnt6', 115200)


n_values = 1000


y0 = np.sin(np.linspace(-10*np.pi, 10*np.pi, n_values))
y1 = np.sin(np.linspace(-1*np.pi, 1*np.pi, n_values))

ya = np.array([y0[i] + y1[i] for i in range(n_values)])

while True:
    data = [j for i in zip(ya) for j in i]  
    data.append(end)
    data = list(sum([(v, sep) for v in data], ()))
    try:
        for v in data:
            ser.write(str(v).encode())
    except SerialException:
        pass
    time.sleep(0.001)
    data = [j for i in zip(y1) for j in i]  
    data.append(end)
    data = list(sum([(v, sep) for v in data], ()))
    try:
        for v in data:
            ser.write(str(v).encode())
    except SerialException:
        pass
    time.sleep(0.001)
