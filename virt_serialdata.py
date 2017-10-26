import serial
import time
import numpy as np
import matplotlib.pylab as plt


sep = ','
end = '\n'


ser = serial.Serial('/dev/tnt6', 9600)


n_values = 1000


y0 = np.sin(np.linspace(-10*np.pi, 10*np.pi, n_values))
y1 = np.sin(np.linspace(-1*np.pi, 1*np.pi, n_values))

ya = np.array([y0[i] + y1[i] for i in range(n_values)])

while True:
    data = [j for i in zip(ya) for j in i]  
    data.append(end)
    data = list(sum([(v, sep) for v in data], ()))
    for v in data:
        ser.write(str(v).encode())
    time.sleep(0.0)
    data = [j for i in zip(y1) for j in i]  
    data.append(end)
    data = list(sum([(v, sep) for v in data], ()))
    for v in data:
        ser.write(str(v).encode())
    time.sleep(0.0)
