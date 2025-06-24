from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
import sys

def window():
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    uic.loadUi('ToolBoxUI.ui', MainWindow)  # Load the UI file
    MainWindow.show()
    sys.exit(app.exec_())