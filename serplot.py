from PyQt5 import QtWidgets, QtCore
#from collections import deque
import pyqtgraph
import sys
import serial
import glob
#import math
#import time
import numpy as np
import queue
#import types
import re

import serplot_ui
#from matplotlib.backends.qt_compat import QtWidgets


settings = {'port': '',
            'baudrate': '115200',
            'n_plots': '3',
            'n_columns': '1',
            'sep': ',',
            'end': '$',
            'xFactor': '1',
            'bufferThr': '0',
            'delaySerial': '3',
            'delayQueue': '3',
            'updateInterval' : '30',
            'serialTimeout' : '300',
            'queueMaxLen': '1000',
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
        except (OSError, serial.serialutil.SerialException):
            pass
    return result        
    


class MainView(QtWidgets.QMainWindow, serplot_ui.Ui_MainWindow):
    
    sigStopSerialThread = QtCore.pyqtSignal()
    sigStopQueueThread = QtCore.pyqtSignal()

    
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)

        pyqtgraph.setConfigOptions(antialias=True)
        self.readSettings()
        self.plots = []
        self.noData = False
        
        self.timerUpdateGraph = QtCore.QTimer()
        self.timerUpdateGraph.setSingleShot(False)
        self.timerUpdateGraph.timeout.connect(self.updatePlots)
        self.timerSerialTimeout = QtCore.QTimer()
        self.timerSerialTimeout.setSingleShot(True)
        self.timerSerialTimeout.timeout.connect(self.showNoData)
        
        self.streamBuffer = queue.Queue()

        self.dataProcessing = False
        
        self.btnApply.clicked.connect(self.startDataProcessing)
        self.btn_clearQueue.clicked.connect(self.clearImgQueue)
        self.btnSaveData.clicked.connect(self.saveData)
        self.comboBoxChooseSerial.showPopup = self.updatePortsBeforePopup
                
                            
    def updatePortsBeforePopup(self):
        self.updateSerialPorts()
        QtWidgets.QComboBox.showPopup(self.comboBoxChooseSerial)  
    
                
    def updateSerialPorts(self):
        self.comboBoxChooseSerial.clear()
        ports = serial_ports();
        for port in ports:
            self.comboBoxChooseSerial.addItem(port)
            
            
    def saveData(self):
        fname = QtWidgets.QFileDialog.getSaveFileName(
            self,"QFileDialog.getSaveFileName()",
            "","All Files (*);;Text Files (*.txt)")
        if fname:
            f = open(fname[0], 'w')
            for data in self.bkp:
                f.write(re.sub('[\[\] ]', '', str(data)) + '\n\r')
        
              
    def readSettings(self):
        self.updateSerialPorts()
        idx = self.comboBoxChooseSerial.findText(settings['port'])
        if idx >= 0:
            self.comboBoxChooseSerial.setCurrentIndex(idx)
        idx = self.comboBoxBaudrate.findText(settings['baudrate'])
        if idx >= 0:
            self.comboBoxBaudrate.setCurrentIndex(idx)
        idx = self.comboBoxNPlots.findText(settings['n_plots'])
        if idx >= 0:
            self.comboBoxNPlots.setCurrentIndex(idx)        
        idx = self.comboBoxNColumns.findText(settings['n_columns'])
        if idx >= 0:
            self.comboBoxNColumns.setCurrentIndex(idx) 
        self.lineEditSeparator.setText(settings['sep'])
        self.lineEditTerminator.setText(settings['end'])
        self.lineEditXFactor.setText(settings['xFactor'])
        self.lineEditSerialDelay.setText(settings['delaySerial'])
        self.lineEditDelayQueue.setText(settings['delayQueue'])
        self.lineEditUpdate.setText(settings['updateInterval'])
        self.lineEditQueueMaxLenght.setText(settings['queueMaxLen'])
        
        
    def startDataProcessing(self):
        if self.dataProcessing:
            self.stopDataProcessing()
        self.writeSettings()
        self.setupPlots()
        self.imgQueue = queue.Queue(maxsize=int(settings['queueMaxLen']))
        self.bkp = []
        self.dataProcessing = True
        self.readSerialBuffer()
        self.readQueue()
        self.startPlotting()
        self.updateView()
        
        
    def writeSettings(self):
        settings['port'] = self.comboBoxChooseSerial.currentText()
        settings['baudrate'] = self.comboBoxBaudrate.currentText()
        settings['n_plots'] = self.comboBoxNPlots.currentText()
        settings['n_columns'] = self.comboBoxNColumns.currentText()
        settings['sep'] = self.lineEditSeparator.text()
        settings['end'] = self.lineEditTerminator.text()
        settings['xFactor'] = float(self.lineEditXFactor.text())
        settings['delaySerial'] = int(self.lineEditSerialDelay.text())
        settings['delayQueue'] = int(self.lineEditDelayQueue.text())   
        settings['updateInterval'] = int(self.lineEditUpdate.text())
        settings['queueMaxLen'] = int(self.lineEditQueueMaxLenght.text())
        
        
    def updateView(self):
        if self.dataProcessing:
            self.groupBoxBuffers.setEnabled(True)
        
        
    def setupPlots(self):
        for p in self.plots:
            self.pltLayout.removeItem(p)
        self.plots = []
        n_plots = int(settings['n_plots'])
        n_columns = int(settings['n_columns'])
        for i in range(n_plots):
            row = i // n_columns
            col = i % n_columns
            p = self.pltLayout.addPlot(row=row, col=col, title=str(i))
            p.showGrid(x=True, y=False)
            self.plots.append(p)    
        self.active_plot = 0
    
                
    def showErrorMsg(self, msg):
        print('<Error>', msg)
    
    
    def showInfoMsg(self, msg):
        self.statusbar.showMessage(msg)
           
    
    def readQueue(self):
        self.queueReader = QueueReader(self)
        self.queueReader.sigDataReady.connect(self.updatePlots)
        self.readQueueThread = QtCore.QThread(self)
        self.queueReader.moveToThread(self.readQueueThread)
        self.readQueueThread.started.connect(self.queueReader.start)
        print('start queue thread')
        self.readQueueThread.start()
        
        
    def startPlotting(self):
        self.pause = False
        self.timerUpdateGraph.start(settings['updateInterval']//len(self.plots))
        self.btnSaveData.setEnabled(False)
        
    
    def stopPlotting(self):
        self.pause = True
        self.btn_run.clicked.connect(self.startPlotting)
        self.btn_run.setText('Run')
        self.btnSaveData.setEnabled(True)
        
        
    @QtCore.pyqtSlot()
    def updatePlots(self):
        self.showStreamBufferSize()
        self.lineEditImgBuffer.setText(str(self.imgQueue.qsize()))
        try:
            if not self.pause:
                self.y_data = self.imgQueue.get(block=False)
                curve = self.plots[self.active_plot].plot(pen='g', clear=True)
                x_data = [x * settings['xFactor'] for x, y in enumerate(self.y_data)]
                curve.setData(x_data, self.y_data)
                self.active_plot = (self.active_plot + 1) % int(settings['n_plots'])
                
                self.bkp.append(self.y_data)
                if len(self.bkp) > int(settings['n_plots']):
                    self.bkp.pop(0)
                
                self.btn_run.clicked.connect(self.stopPlotting)
                self.btn_run.setEnabled(True)
                self.btn_run.setText('Pause')   
        except queue.Empty:
            if not self.dataProcessing or self.noData:
                self.btn_run.setEnabled(False)
                self.btn_run.setText('Run')
        
        
    @QtCore.pyqtSlot()    
    def showStreamBufferSize(self):
        self.lineEditStreamBuffer.setText(str(self.streamBuffer.qsize()))
    
    
    @QtCore.pyqtSlot(int)
    def showBufferLoad(self, n_byte):
        self.lineEditSerialBuffer.setText(str(n_byte))
        if n_byte:
            self.noData = False
            self.showInfoMsg('Receiving data at %s' %settings['port'])
        
        
    @QtCore.pyqtSlot()
    def showNoData(self):
        self.showInfoMsg('No data at %s' %settings['port'])
        self.noData = True
        
        
    @QtCore.pyqtSlot()
    def serialTimeout(self):
        if not self.timerSerialTimeout.isActive():
            self.timerSerialTimeout.start(int(settings['serialTimeout']))
            self.showBufferLoad(0)
    
    
    def readSerialBuffer(self):
        self.serialReader = SerialReader(self)
        self.serialReader.sigBufferLoad.connect(self.showBufferLoad)
        self.serialReader.sigNoData.connect(self.serialTimeout)
        self.serialReader.sigSerialError.connect(self.handleSerialError)
        self.serialThread = QtCore.QThread(self)
        self.serialReader.moveToThread(self.serialThread)
        self.serialThread.started.connect(self.serialReader.start)
        print('start serial thread')
        self.serialThread.start()
       
       
    def stopDataProcessing(self):
        print('stop queue thread')
        self.readQueueThread.quit()
        self.readQueueThread.wait()
        print('stop serial thread')
        self.serialThread.quit()
        self.serialThread.wait()
        self.streamBuffer.queue.clear()
        self.dataProcessing = False  


    @QtCore.pyqtSlot()
    def handleSerialError(self):
        self.stopDataProcessing()
        self.statusbar.showMessage('Check serial port!!')
        self.comboBoxChooseSerial.clear()
        self.timerSerialTimeout.stop()
    
    
    def clearImgQueue(self):
        self.imgQueue.queue.clear()
        if self.noData:
            self.btnSaveData.setEnabled(False)
            self.btn_run.setEnabled(False)
        


class QueueReader(QtCore.QObject):
    
    sigErrorMsg = QtCore.pyqtSignal(object)
    sigDataReady = QtCore.pyqtSignal(object)
    sigQueueCleared = QtCore.pyqtSignal()
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.s_values = []
        self.s_value = ''
        self.streamBuffer = parent.streamBuffer

        
    def readQueue(self):
        f_values = []
        s = ''
        try:
            b = self.streamBuffer.get(block=False)
            s = b.decode('utf-8')
        except UnicodeDecodeError:
            print('can\'t decode bytes!!', b)
        except queue.Empty:
            pass
            
        for c in s:
            if c == settings['sep']:
                if self.s_value:
                    self.s_values.append(self.s_value)
                    self.s_value = ''
            elif c == settings['end']:
                try:
                    f_values = [float(v) for v in self.s_values]
                except ValueError:
                    print('ValueError!!', self.s_values)
                self.parent.imgQueue.put(f_values)
                self.s_values = []
                f_values = []
            else:
                self.s_value += c
        self.timer.start(settings['delayQueue'])
                
                
    def start(self):
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.readQueue)
        self.timer.start(settings['delayQueue'])
       


class SerialReader(QtCore.QObject):
    
    sigNoData = QtCore.pyqtSignal()
    sigBufferLoad = QtCore.pyqtSignal(int)
    sigSerialError = QtCore.pyqtSignal()
    
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.streamBuffer = parent.streamBuffer
        try:
            self.ser = serial.Serial(settings['port'], settings['baudrate'])
        except serial.serialutil.SerialException:
            self.sigSerialError.emit()
    
    
    def readSerialBuffer(self):
        try:
            n_bytes = self.ser.in_waiting
            if n_bytes:
                b = self.ser.read(n_bytes)
                self.streamBuffer.put(b)
                self.sigBufferLoad.emit(n_bytes)
            else:
                self.sigNoData.emit()
        except (serial.serialutil.SerialException, OSError):
            self.sigSerialError.emit()
        self.timer.start(settings['delaySerial'])
    
        
    def start(self):
        self.ser.flushInput()
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.readSerialBuffer)
        self.timer.start(settings['delaySerial'])



if __name__ == '__main__':              
    app = QtWidgets.QApplication(sys.argv)  
    form = MainView()                
    form.show()                        
    app.exec_()                           