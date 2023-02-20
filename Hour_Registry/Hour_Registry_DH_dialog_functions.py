from PyQt5.QtWidgets import QMainWindow, QHeaderView, QDialog
from PyQt5.QtCore import pyqtSignal, Qt, QSettings,  QTime, QDate, QSortFilterProxyModel
from Hour_Registry_DH_dialog_QT import Ui_DH_dialog
from Hour_Registry_SQL import SQL_Database
from Hour_Registry_get_db import Get_db
import pandas as pd
from datetime import datetime, date, timedelta



class DH_dialog(QDialog, Ui_DH_dialog):

    window_closed = pyqtSignal()

    def __init__(self, projects, interval, date, sql_database, columns, parent=None):
        super(DH_dialog, self).__init__(parent)
        self.setupUi(self)
        self.comboBox_project_add.addItems(projects)
        self.cols_dh = columns
        self.hour_database = sql_database
        self.date = date
        self.start = interval.split("-")[0]
        self.end = interval.split("-")[1]
        self.pop_lineedits(date, self.start, self.end)

    def closeEvent(self, event):
        self.window_closed.emit()
        event.accept()

    def pop_lineedits(self, date, start, end):
        df = Get_db.get_daily_edit_db(self, date, start, end, self.cols_dh)
        self.dateEdit.setDate(QDate.fromString(df["Date"][0], 'yyyy-MM-dd'))
        self.timeEdit_start.setTime(QTime.fromString(df["Start"][0]))
        self.timeEdit_end.setTime(QTime.fromString(df["End"][0]))
        self.comboBox_project_add.setCurrentText(df["Project_ID"][0])
        self.lineEdit_add_info.setText(df["Additional_information_dh"][0])

    def date_now(self):
        date_now = QDate.currentDate()
        self.dateEdit.setDate(date_now)

    def start_now(self):
        start_now = QTime.currentTime()
        self.timeEdit_start.setTime(start_now)

    def end_now(self):
        end_now = QTime.currentTime()
        self.timeEdit_end.setTime(end_now)

    def duration(self):
        self.t_start = self.timeEdit_start.time().toString("hh:mm")
        self.t_end = self.timeEdit_end.time().toString("hh:mm")
        format = '%H:%M'
        duration = str(datetime.strptime(self.t_end, format) - datetime.strptime(self.t_start, format))
        self.label_duration_time.setText(duration)


    def edit_daily(self):
        """
        :return: Edit record equal to the LineEdit inputs
        """
        self.duration()
        db =  SQL_Database(f"{self.hour_database}")

        sql = """Update daily set 
        Date=?, 
        Start=?, 
        End=?, 
        Duration=?, 
        Project_ID=?, 
        Additional_information_dh=? 
        WHERE Date = ? AND Start = ? AND End = ? """
        parameters =(self.dateEdit.date().toString(Qt.ISODate),
                     self.timeEdit_start.time().toString("hh:mm"),
                     self.timeEdit_end.time().toString("hh:mm"),
                     self.label_duration_time.text(),
                     self.comboBox_project_add.currentText(),
                     self.lineEdit_add_info.text(),
                     self.date,
                     self.start,
                     self.end)

        db.execute(sql, parameters)
        db.commit()
        db.close
        self.close()














