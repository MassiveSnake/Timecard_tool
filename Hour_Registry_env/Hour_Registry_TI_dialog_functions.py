from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal
from QT_Files.Hour_Registry_TI_dialog_QT import Ui_TaskInput_edit_dialog
from Hour_Registry_Settings_dialog_functions import Settings_dialog
from Hour_Registry_SQL import SQL_Database
from Hour_Registry_get_db import Get_db


class TaskInput_edit_dialog(QDialog, Ui_TaskInput_edit_dialog):
    window_closed = pyqtSignal()

    def __init__(self, project_name: object, task_name: object, sql_database: object, pcolumns: object, tcolumns: object, parent: object = None) -> object:
        super(TaskInput_edit_dialog, self).__init__(parent)
        self.setupUi(self)
        self.project_input_columns = pcolumns
        self.task_input_columns = tcolumns
        self.project_name = project_name
        self.task_name = task_name
        self.local_database = sql_database
        a, b, c, self.currency, e, f = Settings_dialog.set_settings(self)

        self.pop_lineedits()

    def name_number_changed(self):
        name = self.lineEdit_task_name.text()
        number = self.lineEdit_task_number.text()
        oracle_name = number + " - " + name
        self.lineEdit_Oracle_name.setText(oracle_name)

    def changed_billable_toggle(self):
        """
        QCheckbox with a toggle layout
        :return:
        disable or enable LineEdit fields within Project Input
        """
        check = self.checkBox_billable.isChecked()
        if check:
            self.label_hourly_rate.setDisabled(False)
            self.lineEdit_hourly_rate.setDisabled(False)

        else:
            self.lineEdit_hourly_rate.setText("0")
            self.label_hourly_rate.setDisabled(True)
            self.lineEdit_hourly_rate.setDisabled(True)

    def closeEvent(self, event):
        self.window_closed.emit()
        event.accept()

    def pop_lineedits(self):
        df_p = Get_db.get_project_edit_db(self, self.local_database, self.project_name, self.project_input_columns)
        df_t = Get_db.get_task_edit_db(self, self.local_database, self.project_name, self.task_name, self.task_input_columns)

        self.label_project_name_description.setText(df_p["Project_Name"][0])
        self.label_project_number_description.setText(df_p["Project_Number"][0])
        self.lineEdit_task_name.setText(df_t["Task_Name"][0])
        self.lineEdit_task_number.setText(df_t["Task_Number"][0])
        self.lineEdit_Oracle_name.setText(df_t["Oracle_Name_ti"][0])
        self.checkBox_billable.setCheckState(int(df_t["Billable"][0]))
        self.lineEdit_hourly_rate.setText(df_t["Hourly_Rate"][0])
        self.comboBox_currency.setCurrentText(self.currency)
        self.lineEdit_additional_information.setText(df_t["Comment_ti"][0])

    def edit_task(self):
        """
        :return: Edit record equal to the LineEdit inputs
        """
        db = SQL_Database(f"{self.local_database}")

        sql = f"""Update '{self.project_name}' set 
        Task_Number=?,
        Oracle_Name_ti=?, 
        Billable=?,
        Hourly_Rate=?,
        Currency=?, 
        Comment_ti=? 
        where Task_Name = ?"""
        try:
            float(self.lineEdit_hourly_rate.text())
        except ValueError:
            type = "Unvalid Hourly Rate"
            text = "Only float and integers are valid hourly rates"
            info = "Use . as delimiter"
            self.messagebox(type, text, info)
            return None

        parameters =    (self.lineEdit_task_number.text(),
                         self.lineEdit_Oracle_name.text(),
                        int(self.checkBox_billable.isChecked()),
                        self.lineEdit_hourly_rate.text(),
                        self.comboBox_currency.currentText(),
                        self.lineEdit_additional_information.text(),
                        self.task_name)
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
