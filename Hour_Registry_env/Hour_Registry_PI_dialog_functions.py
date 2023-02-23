from PyQt5.QtWidgets import QMainWindow, QHeaderView, QDialog
from PyQt5.QtCore import pyqtSignal, Qt, QSettings,  QTime, QDate, QSortFilterProxyModel
from Hour_Registry_PI_dialog_QT import Ui_ProjectInput_edit_dialog
from Hour_Registry_SQL import SQL_Database
from Hour_Registry_get_db import Get_db



class ProjectInput_edit_dialog(QDialog, Ui_ProjectInput_edit_dialog):

    window_closed = pyqtSignal()

    def __init__(self, project_id, sql_database, columns, parent=None):
        super(ProjectInput_edit_dialog, self).__init__(parent)
        self.setupUi(self)
        self.project_input_columns = columns
        self.project_id = project_id
        self.hour_database = sql_database

        self.pop_lineedits()

    def closeEvent(self, event):
        self.window_closed.emit()
        event.accept()

    def billable_changed(self):
        check = self.checkBox_billable.isChecked()
        if check == True:
            self.label_rate.setDisabled(False)
            self.lineEdit_rate.setDisabled(False)
            self.comboBox_currency.setDisabled(False)
        else:
            self.lineEdit_hourly_rate.setText("0")
            self.label_hourly_rate.setDisabled(True)
            self.lineEdit_hourly_rate.setDisabled(True)
            self.comboBox_currency.setDisabled(True)

    def pop_lineedits(self):
        df = Get_db.get_project_edit_db(self, self.project_id, self.project_input_columns)

        self.lineEdit_client.setText(df["Client"][0])
        self.lineEdit_project_name.setText(df["Project_Name"][0])
        self.lineEdit_project_number.setText(str(df["Project_Number"][0]))
        self.lineEdit_task_number.setText(df["Task_Number"][0])
        self.lineEdit_hourly_rate.setText(str(df["Hourly_Rate"][0]))
        self.comboBox_currency.setCurrentText(df["Currency"][0])
        self.lineEdit_project_manager.setText(df["Project_Manager"][0])
        self.lineEdit_client_contact.setText(df["Client_Contact"][0])
        self.lineEdit_additional_information.setText(df["Additional_information_pi"][0])

    def edit_project(self):
        """
        :return: Edit record equal to the LineEdit inputs
        """
        db = SQL_Database(f"{self.hour_database}")

        sql = """Update projects set 
        Project_Number=?, 
        Task_Number=?, 
        Hourly_Rate=?, 
        Currency=?, 
        Project_Manager=?, 
        Client_Contact=?, 
        Additional_information_pi=? 
        where id_pi = ?"""
        parameters =(self.lineEdit_project_number.text(),
                     self.lineEdit_task_number.text(),
                     self.lineEdit_hourly_rate.text(),
                     self.comboBox_currency.currentText(),
                     self.lineEdit_project_manager.text(),
                     self.lineEdit_client_contact.text(),
                     self.lineEdit_additional_information.text(),
                     self.project_id)
        db.execute(sql, parameters)
        db.commit()
        db.close
        self.close()










