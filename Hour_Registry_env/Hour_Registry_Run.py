from PyQt5.QtWidgets import QApplication
from Hour_Registry_Functions import MyMainWindow

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    MainWindow = MyMainWindow()
    #MainWindow.resize_table_to_contents()
    MainWindow.show()
    sys.exit(app.exec_())
