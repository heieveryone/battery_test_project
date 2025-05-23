# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'test.ui'
#
# Created by: PyQt5 UI code generator 5.15.11
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.

import os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QVBoxLayout, QPushButton, QWidget, QLabel, QListWidget, QAbstractItemView
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1000, 700)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(150, 50, 258, 238))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.choose_label = QtWidgets.QLabel(self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setFamily("Arial Black")
        font.setPointSize(9)
        font.setBold(True)
        font.setWeight(75)
        self.choose_label.setFont(font)
        self.choose_label.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.choose_label.setAlignment(QtCore.Qt.AlignCenter)
        self.choose_label.setObjectName("choose_label")
        self.verticalLayout.addWidget(self.choose_label)
        self.choose_folder_pushButton = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.choose_folder_pushButton.setObjectName("choose_folder_pushButton")
        self.choose_folder_pushButton.clicked.connect(self.openFolder)
        self.verticalLayout.addWidget(self.choose_folder_pushButton)
        self.csv_list = QtWidgets.QListWidget(self.verticalLayoutWidget)
        self.csv_list.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.csv_list.setObjectName("csv_list")
        self.verticalLayout.addWidget(self.csv_list)
        self.plot_one_pushButton = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.plot_one_pushButton.setObjectName("plot_one_pushButton")
        self.verticalLayout.addWidget(self.plot_one_pushButton)
        self.plot_seperate_pushButton = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.plot_seperate_pushButton.setObjectName("plot_seperate_pushButton")
        self.verticalLayout.addWidget(self.plot_seperate_pushButton)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 519, 18))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.choose_folder_pushButton.clicked.connect(self.csv_list.clear) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.choose_label.setText(_translate("MainWindow", "Choose folder and csv file"))
        self.choose_folder_pushButton.setText(_translate("MainWindow", "Choose folder"))
        self.plot_one_pushButton.setText(_translate("MainWindow", "plot in one figure"))
        self.plot_seperate_pushButton.setText(_translate("MainWindow", "plot seperate figure"))

    def openFolder(self):
        folder = QFileDialog.getExistingDirectory(self, 'choose_folder_pushButton')
        if folder:
            self.listWidget.clear()
            self.folder = folder
            for filename in os.listdir(folder):
                if filename.endswith('.csv'):
                    self.listWidget.addItem(filename)
    
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
