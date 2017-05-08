#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Author: Shunya Sato
# Copyright (c) 2017 Shunya Sato
#
# MIT Lisence
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
Recommend to run this with anaconda.

conda create -n watt_up python=3.6 pyqt numpy matplotlib seaborn pyserial
source activate watt_up

python watt_up.pyw

"""

import sys

import serial
import numpy as np

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
import seaborn as sns # to make plot pretty

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.uic import loadUiType

#from ui_haptSynth import Ui_MainWindow
Ui_MainWindow, QMainWindow = loadUiType('watt_up.ui')

class SerialWorker(QtCore.QObject):
    # http://stackoverflow.com/questions/6783194/background-thread-with-qthread-in-pyqt
    finished = QtCore.pyqtSignal()
    dataReady = QtCore.pyqtSignal(bytes)

    def __init__(self):
        super(SerialWorker, self).__init__()
        self.addr  = "COM1"
        self.baud  = 9600 #115200
        self.running = False
        self.port = None
        self.fname = "log.txt"
        self.use_file = False

    @QtCore.pyqtSlot()
    def processA(self):
        print("SerialWorker.processA")
        if self.use_file:
            self.port = open(self.fname, "r")
        else:
            try:
                print("Try opening serial port: {}".format(self.addr))
                self.port = serial.Serial(self.addr,self.baud)
            except:
                print("Error opening serial port!")
                self.port = None
                return None
        print("opened port")
        while self.running:
            #print "SerialWorker is running"
            line = self.port.readline()
            #line = self.port.read()
            # line is bytes
            #print("Received: {}".format(line))
            self.dataReady.emit(line)
            if self.use_file:
                time.sleep(0.01)

        print("SerialWorker finished processA")
        self.port.close()
        print("port is closed")
        self.finished.emit()

    def startRunning(self, portname):
        if portname == "FILE":
            self.use_file = True
        else:
            self.use_file = False
            self.addr = portname
        self.running = True

    def stopRunning(self):
        self.running = False

    def setFilename(self, fname):
        self.fname = fname

    def write(self, data):
        # data must be bytes
        if self.running:
            print("Writing: {}".format(data))
            self.port.write(data)

    def __del__(self):
        self.running = False
        if self.port:
            self.port.close()

class MainWindow(QMainWindow, Ui_MainWindow):
    """
    """
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.running = False

        self.thread = QtCore.QThread()  # no parent!
        self.serialreader = SerialWorker()  # no parent!
        self.serialreader.moveToThread(self.thread)
        self.serialreader.dataReady.connect(self.processPayload)
        self.thread.started.connect(self.serialreader.processA)

        self.pushButton_open.clicked.connect(self.onPushButton_open)
        self.pushButton_update.clicked.connect(self.populatePort)
        self.label_dummy.setVisible(False)
        self.lcdNumber_dummy.setVisible(False)
        self.lcdNumber_temp.setVisible(False)
        self.label_11.setVisible(False)
        self.label_10.setVisible(False)
        #self.label_dummy2.setVisible(False)
        self.lcds = [self.lcdNumber_win,
                    self.lcdNumber_wout,
                    self.lcdNumber_efficiency,
                    self.lcdNumber_temp,
                    self.lcdNumber_coil
                    ]

        self.populatePort()

        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.datas = []
        self.lines = []
        self.x_array = np.linspace(-300, 0, num=301, endpoint=True)
        for i in range(5):
            data = np.zeros(301)
            self.datas.append(data)
            line, = self.ax.plot(self.x_array, data)
            self.lines.append(line)
        self.addmpl(self.fig)
        self.updatePlot()

    def addmpl(self, fig):
        self.canvas = FigureCanvas(fig)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas,
                self.widget_mpl, coordinates=True)
        vbox.addWidget(self.toolbar)
        self.widget_mpl.setLayout(vbox)
        self.canvas.draw()

    def updatePlot(self):
        pass

    def onPushButton_open(self):
        if not self.running:
            print("Start running!")
            self.serialreader.startRunning(str(self.comboBox_serial.currentText()))
            self.thread.start()
            self.running = True
            self.pushButton_open.setText("CLOSE")

        else:
            print("Stop running.")
            self.serialreader.stopRunning()
            self.thread.quit()
            self.running = False
            self.pushButton_open.setText("OPEN")

    def processPayload(self, payloadBytes):
        """
        Receive payload as Byte
        """
        payload = payloadBytes.decode("utf-8")
        # insert at end
        self.textBrowser_log.moveCursor(QtGui.QTextCursor.End)
        self.textBrowser_log.insertPlainText(payload)
        # append with implicit new line
        #self.textBrowser_log.append(payload.strip())
        #if self.checkBox_autoscroll.isChecked():
        #    self.textBrowser_log.moveCursor(QtGui.QTextCursor.End)
        try:
            values = payload.strip().split(",")
            if len(values) == len(self.lcds):
                for i in range(len(values)):
                    self.lcds[i].display(values[i])
                    self.datas[i] = np.append(self.datas[i][1:], float(values[i]))
                    self.lines[i].set_data(self.x_array, self.datas[i])
                self.ax.relim()
                self.ax.autoscale_view(True,True,True)
                self.canvas.draw()
        except Exception as e:
            print(e)

    def populatePort(self):
        self.comboBox_serial.clear()
        serials = []
        import serial.tools.list_ports
        #print list(serial.tools.list_ports.comports())
        serials += list(serial.tools.list_ports.comports())
        #print(serials)
        for device in serials:
            self.comboBox_serial.addItem(device[0])
        # TODO: list_ports doesn't work under conda env ...?
        if len(serials)==0:
            self.comboBox_serial.addItem("/dev/cu.usbmodem1411")

        # select last one as default
        nports = self.comboBox_serial.count()
        if nports != 0:
            self.comboBox_serial.setCurrentIndex(nports-1)

    def __del__(self):
        # make sure serial is closed.
        #super(MainWindow, self).__del__(parent)
        self.serialreader.stopRunning()
        self.thread.quit()

    def closeEvent(self, event):
        pass

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("watt_up")
    form = MainWindow()
    form.show()
    app.exec_()
