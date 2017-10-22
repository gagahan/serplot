# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'serplot.main.ui'
#
# Created by: PyQt5 UI code generator 5.8
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.btnPlay = QtWidgets.QPushButton(self.centralwidget)
        self.btnPlay.setEnabled(False)
        self.btnPlay.setMinimumSize(QtCore.QSize(782, 0))
        self.btnPlay.setObjectName("btnPlay")
        self.gridLayout.addWidget(self.btnPlay, 1, 0, 1, 1, QtCore.Qt.AlignRight)
        self.pltLayout = GraphicsLayoutWidget(self.centralwidget)
        self.pltLayout.setObjectName("pltLayout")
        self.gridLayout.addWidget(self.pltLayout, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")
        self.menuMenu = QtWidgets.QMenu(self.menubar)
        self.menuMenu.setObjectName("menuMenu")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionSettings = QtWidgets.QAction(MainWindow)
        self.actionSettings.setObjectName("actionSettings")
        self.menuMenu.addAction(self.actionSettings)
        self.menubar.addAction(self.menuMenu.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.btnPlay.setText(_translate("MainWindow", "Play"))
        self.menuMenu.setTitle(_translate("MainWindow", "Menu"))
        self.actionSettings.setText(_translate("MainWindow", "Settings"))
        self.actionSettings.setShortcut(_translate("MainWindow", "Ctrl+S"))

from pyqtgraph import GraphicsLayoutWidget
