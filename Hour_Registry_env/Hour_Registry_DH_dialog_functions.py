from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import pyqtSignal, Qt, QTime, QDate
from QT_Files.Hour_Registry_DH_dialog_QT import Ui_DailyHours_edit_dialog
from Hour_Registry_SQL import SQL_Database
from Hour_Registry_get_db import Get_db
from datetime import datetime


class DailyHours_edit_dialog(QDialog, Ui_DailyHours_edit_dialog):

    window_closed = pyqtSignal()

    def __init__(self, projects, interval, date, sql_database, columns, parent=None):
        super(DailyHours_edit_dialog, self).__init__(parent)
        self.setupUi(self)
        self.comboBox_project_select.addItems(projects)
        self.daily_hours_columns = columns
        self.hour_database = sql_database
        self.date = date
        self.start = interval.split("-")[0]
        self.end = interval.split("-")[1]
        self.pop_lineedits(date, self.start, self.end)

    def closeEvent(self, event):
        self.window_closed.emit()
        event.accept()

    def pop_lineedits(self, date, start, end):
        df = Get_db.get_daily_edit_db(self, date, start, end, self.daily_hours_columns)
        self.dateEdit.setDate(QDate.fromString(df["Date"][0], 'yyyy-MM-dd'))
        self.timeEdit_start.setTime(QTime.fromString(df["Start"][0]))
        self.timeEdit_end.setTime(QTime.fromString(df["End"][0]))
        self.comboBox_project_select.setCurrentText(df["Project_ID"][0])
        self.lineEdit_additional_information.setText(df["Additional_information_dh"][0])

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
        start_time = self.timeEdit_start.time().toString("hh:mm")
        end_time = self.timeEdit_end.time().toString("hh:mm")
        format = '%H:%M'
        duration = str(datetime.strptime(end_time, format) - datetime.strptime(start_time, format))
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
                     self.comboBox_project_select.currentText(),
                     self.lineEdit_additional_information.text(),
                     self.date,
                     self.start,
                     self.end)

        db.execute(sql, parameters)
        db.commit()
        db.close
        self.close()














