from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import pyqtSignal
from QT_Files.Hour_Registry_PI_dialog_QT import Ui_ProjectInput_edit_dialog
from Hour_Registry_SQL import SQL_Database
from Hour_Registry_get_db import Get_db


class ProjectInput_edit_dialog(QDialog, Ui_ProjectInput_edit_dialog):
    window_closed = pyqtSignal()

    def __init__(self, project_name: object, sql_database: object, columns: object, parent: object = None) -> object:
        super(ProjectInput_edit_dialog, self).__init__(parent)
        self.setupUi(self)
        self.project_input_columns = columns
        self.project_name = project_name
        self.local_database = sql_database

        self.pop_lineedits()
    def name_number_changed(self):
        name = self.lineEdit_project_name.text()
        number = self.lineEdit_project_number.text()
        oracle_name = number + " - " + name
        self.lineEdit_Oracle_name.setText(oracle_name)

    def closeEvent(self, event):
        self.window_closed.emit()
        event.accept()

    def pop_lineedits(self):
        df = Get_db.get_project_edit_db(self, self.local_database, self.project_name, self.project_input_columns)

        self.lineEdit_client.setText(df["Client"][0])
        self.lineEdit_project_name.setText(df["Project_Name"][0])
        self.lineEdit_project_number.setText(str(df["Project_Number"][0]))
        self.lineEdit_Oracle_name.setText(str(df["Oracle_Name_pi"][0]))
        self.lineEdit_project_manager.setText(df["Project_Manager"][0])
        self.lineEdit_client_contact.setText(df["Client_Contact"][0])
        self.lineEdit_additional_information.setText(df["Additional_information_pi"][0])

    def edit_project(self):
        """
        :return: Edit record equal to the LineEdit inputs
        """
        db = SQL_Database(f"{self.local_database}")

        sql = """Update projects set 
        Client=?,
        Project_Number=?, 
        Oracle_Name_pi=? ,
        Project_Manager=?, 
        Client_Contact=?, 
        Additional_information_pi=? 
        where Project_Name = ?"""
        parameters = (self.lineEdit_client.text(),
                      self.lineEdit_project_number.text(),
                      self.lineEdit_Oracle_name.text(),
                      self.lineEdit_project_manager.text(),
                      self.lineEdit_client_contact.text(),
                      self.lineEdit_additional_information.text(),
                      self.project_name)
        db.execute(sql, parameters)
        db.commit()
        db.close
        self.close()
