from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import sys
import serial
import glob
import math
import numpy as np

import serplot_ui
import diagSettings



settings = {'port': '',
            'baudrate': '',
            'n_plots': '4'}



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
        self.collectSettings()
        self.updateView()
        
        
    def collectSettings(self):
        settings['port'] = self.comboBoxChooseSerial.currentText()
        settings['baudrate'] = self.comboBoxBaudrate.currentText()
        settings['n_plots'] = self.comboBoxNPlots.currentText()

        
    def updateView(self):
        self.btnApply.setEnabled(True)
        for value in settings.values():
            if not value:
                self.btnApply.setEnabled(False)
                
        
    def applySettings(self):
        self.collectSettings()
        self.parent.buildPlots()
        self.parent.readData()
        #self.destroy()



class MainView(QtWidgets.QMainWindow, serplot_ui.Ui_MainWindow):
    
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)
        self.actionSettings.triggered.connect(self.openSettingsDiag)
        self.openSettingsDiag()
        pg.setConfigOptions(antialias=True)
        self.plots = []
        '''
        plt = self.pltLayout.addPlot()
        curve = plt.plot(pen='g')
        data = np.random.normal(size=100)
        curve.setData(data)
        '''


    def openSettingsDiag(self):
        self.diagSettings = DiagSettings(self)
        self.diagSettings.show()
        
        
    def buildPlots(self):
        for p in self.plots:
            self.pltLayout.removeItem(p)
        self.plots = []
        n_plots = int(settings['n_plots'])
        for i in range(n_plots):
            self.plots.append(self.pltLayout.addPlot(title=str(i)))
            self.pltLayout.nextRow()
        
        
        for plt in self.plots:
            data = np.random.normal(size=100)
            curve = plt.plot(pen='g')
            curve.setData(data)
    
    
    def readData(self):
        if self.plots:
            self.serialReader = SerialReader()
            self.serialThread = QtCore.QThread()
            self.serialReader.moveToThread(self.serialThread)
            self.serialReader.sigLineDone.connect(self.updatePlots)
            self.serialReader.sigValueError.connect(self.errorMsg)
            self.serialThread.started.connect(self.serialReader.readData)
            self.serialThread.start()
            

class SerialReader(QtCore.QObject):
    
    sigLineDone = QtCore.pyqtSignal(object)
    sigValueError = QtCore.pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
    
    def readData(self):
        line = ''
        values = []
        self.ser = serial.Serial(settings['port'], settings['baudrate'])
        while True:
            line += self.ser.read()
            if line[-1] == settings['stop']:
                for s in line.split(settings['sep']):
                    try:
                        values.append(float(s))
                    except ValueError:
                        self.sigValueError.emit(s)
                self.sigLineDone.emit(values)
                   
                   

if __name__ == '__main__':              
    app = QtWidgets.QApplication(sys.argv)  
    form = MainView()                
    form.show()                        
    app.exec_()                     
                            