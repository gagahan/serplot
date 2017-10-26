from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import sys
import serial
import glob
import math
import time
import numpy as np
import queue

import serplot_ui
import diagSettings



settings = {'port': '',
            'baudrate': '',
            'n_plots': '3',
            'sep': ',',
            'end': '\n',
            'mode': 'normal'}



def serial_ports():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        ports = glob.glob('/dev/tty[A-Za-z]*')
        ports += glob.glob('/dev/tnt*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')
    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result



class DiagSettings(QtWidgets.QDialog, diagSettings.Ui_dialogSettings):
    
    def __init__(self, parent=None):
        super(self.__class__, self).__init__()
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        self.parent = parent
        self.btnApply.clicked.connect(self.applySettings)
        self.comboBoxChooseSerial.clear()
        for port in serial_ports():
            self.comboBoxChooseSerial.addItem(port)
        self.writeSettings()
        self.updateView()
        
        
    def writeSettings(self):
        settings['port'] = self.comboBoxChooseSerial.currentText()
        settings['baudrate'] = self.comboBoxBaudrate.currentText()
        settings['n_plots'] = self.comboBoxNPlots.currentText()


    def updateView(self):
        self.btnApply.setEnabled(True)
        for value in settings.values():
            if not value:
                self.btnApply.setEnabled(False)

        
    def applySettings(self):
        if self.parent.dataProcessing:
            self.parent.stopDataProcessing()
        self.writeSettings()
        self.parent.setupPlots()
        self.parent.dataProcessing = True
        self.parent.readQueue()
        self.parent.readSerialBuffer()
        self.destroy()
    


class MainView(QtWidgets.QMainWindow, serplot_ui.Ui_MainWindow):
    
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)
        self.actionSettings.triggered.connect(self.openSettingsDiag)
        self.openSettingsDiag()
        pg.setConfigOptions(antialias=True)
        self.plots = []
        self.d_queue = queue.Queue()
        self.dataProcessing = False
        self.ser_closed = True
        self.queue_cleared = True
        
        
    @QtCore.pyqtSlot(int)
    def openSettingsDiag(self):
        self.diagSettings = DiagSettings(self)
        self.diagSettings.show()
        
        
    def setupPlots(self):
        for p in self.plots:
            self.pltLayout.removeItem(p)
        self.plots = []
        n_plots = int(settings['n_plots'])
        for i in range(n_plots):
            self.plots.append(self.pltLayout.addPlot(title=str(i)))
            self.pltLayout.nextRow()
        self.active_plot = 0
    
                
    @QtCore.pyqtSlot(int)
    def showErrorMsg(self, msg):
        print('<Error>', msg)
    
    
    @QtCore.pyqtSlot(int)
    def showInfoMsg(self, msg):
        print('<Info>', msg)
    
    
    def readQueue(self):   
        self.queueReader = QueueReader(self)
        self.queueReader.sigDataReady.connect(self.updatePlots)
        self.queueReader.sigQueueCleared.connect(self.showInfoMsg)
        self.readQueueThread = QtCore.QThread(self)
        self.queueReader.moveToThread(self.readQueueThread)
        self.readQueueThread.started.connect(self.queueReader.readQueue)
        self.readQueueThread.start()
        
    
    @QtCore.pyqtSlot(int)
    def updatePlots(self, data):
        curve = self.plots[self.active_plot].plot(pen='g', clear=True)
        curve.setData(data)
        if settings['mode'] == 'normal':
            pass
        self.active_plot = (self.active_plot + 1) % int(settings['n_plots'])
        #print('queue:', self.d_queue.qsize())
    
    
    def readSerialBuffer(self):
        self.serialReader = SerialReader(self)
        self.serialThread = QtCore.QThread(self)
        self.serialReader.moveToThread(self.serialThread)
        self.serialThread.started.connect(self.serialReader.readSerialBuffer)
        self.serialThread.start()
       
       
    def stopDataProcessing(self):
        print('stop data processing')
        self.serialReader.stop()
        while(not self.ser_closed):
            pass
        self.serialThread.quit()
        self.serialThread.wait()
        
        self.queueReader.stop()
        while(not self.queue_cleared):
            pass
        self.readQueueThread.quit()
        self.readQueueThread.wait()     

            

class QueueReader(QtCore.QObject):
    
    sigErrorMsg = QtCore.pyqtSignal(object)
    sigDataReady = QtCore.pyqtSignal(object)
    sigQueueCleared = QtCore.pyqtSignal(object)
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self._is_running = True
        parent.queue_cleared = False
        self.d_queue = parent.d_queue

        
    def readQueue(self):
        f_values = []
        s_values = []
        s_value = ''
        while self._is_running:
            time.sleep(0.02)
            s = self.d_queue.get().decode('utf-8')
            #print('queue read', s)
            for c in s:
                if c == settings['sep']:
                    if s_value:
                        s_values.append(s_value)
                        s_value = ''
                elif c == settings['end']:
                    try:
                        f_values = [float(v) for v in s_values]
                    except ValueError:
                        print('ValueError!!', s_values)
                        pass
                    self.sigDataReady.emit(f_values)
                    s_values = []   
                    f_values = []
                else:
                    s_value += c
        self.d_queue.queue.clear()
        self.parent.queue_cleared = True
        print('queue cleared!!')
        #self.sigQueueCleared.emit('queue is cleared. Thread is ready to quit!')
       
       
    def stop(self):
        self._is_running = False   
        
            

class SerialReader(QtCore.QObject):
    
    sigSerClosed = QtCore.pyqtSignal(object)
    sigBufferFull = QtCore.pyqtSignal(object)
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self._is_running = True
        parent.ser_closed = False
        self.d_queue = parent.d_queue
    
    
    def readSerialBuffer(self):
        cnt = 0
        self.ser = serial.Serial(settings['port'], settings['baudrate'])
        self.ser.flushInput()
        while self._is_running:
            
            n_bytes = self.ser.in_waiting
            if n_bytes > 100:
                s = self.ser.read(n_bytes)
                self.d_queue.put(s)
                if n_bytes > 4000:
                    print('buffer:', n_bytes)
            time.sleep(0.001)
        self.ser.close()
        self.parent.ser_closed = True
        print('serial closed')
        #self.sigSerClosed.emit('Serial Port is Closed. Thread is ready to quit!')

    
    def stop(self):
        self._is_running = False



if __name__ == '__main__':              
    app = QtWidgets.QApplication(sys.argv)  
    form = MainView()                
    form.show()                        
    app.exec_()                           