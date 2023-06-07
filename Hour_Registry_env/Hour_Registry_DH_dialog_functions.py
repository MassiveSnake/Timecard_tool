from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal, Qt, QTime, QDate
from QT_Files.Hour_Registry_DH_dialog_QT import Ui_DailyHours_edit_dialog
from Hour_Registry_SQL import SQL_Database
from Hour_Registry_get_db import Get_db
from datetime import datetime


class DailyHours_edit_dialog(QDialog, Ui_DailyHours_edit_dialog):

    window_closed = pyqtSignal()

    def __init__(self, projects, interval, date, sql_database, daily_columns, task_columns, parent=None):
        super(DailyHours_edit_dialog, self).__init__(parent)
        self.setupUi(self)

        self.daily_hours_columns = daily_columns
        self.task_columns = task_columns
        self.local_database = sql_database
        self.date = date
        self.start = interval.split("-")[0]
        self.end = interval.split("-")[1]
        self.comboBox_project_select.addItems(projects)
        self.pop_lineedits(date, self.start, self.end)

    def closeEvent(self, event):
        self.window_closed.emit()
        event.accept()

    def pop_lineedits(self, date, start, end):
        df = Get_db.get_daily_edit_db(self, self.local_database, date, start, end, self.daily_hours_columns)
        self.dateEdit.setDate(QDate.fromString(df["Date"][0], 'yyyy-MM-dd'))
        self.timeEdit_end.setTime(QTime.fromString(df["End"][0]))
        self.timeEdit_start.setTime(QTime.fromString(df["Start"][0]))
        self.label_duration_time.setText(df["Duration"][0])
        self.comboBox_project_select.setCurrentText(df["Project_Name"][0])
        self.comboBox_task_select.setCurrentText(df["Task_Name"][0])
        self.lineEdit_additional_information.setText(df["Comment_dh"][0])

    def date_now(self):
        date_now = QDate.currentDate()
        self.dateEdit.setDate(date_now)

    def start_now(self):
        start_now = QTime.currentTime()
        self.timeEdit_end.setTime(end_now)
        self.timeEdit_start.setTime(start_now)

    def end_now(self):
        end_now = QTime.currentTime()
        self.timeEdit_end.setTime(end_now)

    def add_min(self):
        end_time = self.timeEdit_end.time()
        added_delta = end_time.addSecs(15 * 60)
        self.timeEdit_end.setTime(added_delta)

    def add_hour(self):
        end_time = self.timeEdit_end.time()
        added_delta = end_time.addSecs(60 * 60)
        self.timeEdit_end.setTime(added_delta)

    def duration(self):
        start_time = self.timeEdit_start.time().toString("hh:mm")
        end_time = self.timeEdit_end.time().toString("hh:mm")
        format = '%H:%M'
        duration = str(datetime.strptime(end_time, format) - datetime.strptime(start_time, format))
        invalid_duration = duration.startswith("-")
        try:
            if  invalid_duration == True:
                raise ValueError
            else:
                self.label_duration_time.setText(duration)
        except ValueError:
            type = "Negative Duration"
            text = "Duration Time cannot be negative"
            info = "Please correct the start or end time"
            self.messagebox(type, text, info)
            return None
    def project_select_changed(self):
        project = self.comboBox_project_select.currentText()
        self.comboBox_task_select.clear()
        df_t = Get_db.get_task_db(self, self.local_database, project, self.task_columns)
        if df_t.empty:
            pass
        else:
            self.comboBox_task_select.addItems(df_t["Task_Name"].values)

    def edit_daily(self):
        """
        :return: Edit record equal to the LineEdit inputs
        """
        try:
            self.duration()
        except ValueError:
            type = "Negative Duration"
            text = "Duration Time cannot be negative"
            info = "Please correct the start or end time"
            self.messagebox(type, text, info)
            return None

        db =  SQL_Database(f"{self.local_database}")

        sql = """Update daily set 
        Date=?, 
        Start=?, 
        End=?, 
        Duration=?, 
        Project_Name=?,
        Task_Name=?, 
        Comment_dh=? 
        WHERE Date = ? AND Start = ? AND End = ? """
        parameters =(self.dateEdit.date().toString(Qt.ISODate),
                     self.timeEdit_start.time().toString("hh:mm"),
                     self.timeEdit_end.time().toString("hh:mm"),
                     self.label_duration_time.text(),
                     self.comboBox_project_select.currentText(),
                     self.comboBox_task_select.currentText(),
                     self.lineEdit_additional_information.text(),
                     self.date,
                     self.start,
                     self.end)

        db.execute(sql, parameters)
        db.commit()
        db.close
        self.close()
    def messagebox(self, type, text, info):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Error:  " + type)
        msg.setText(text)
        msg.setInformativeText(info)
        msg.exec()
        return None














