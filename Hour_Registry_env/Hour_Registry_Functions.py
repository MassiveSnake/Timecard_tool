import sqlite3
from PyQt5.QtWidgets import QMainWindow, QHeaderView, QFileDialog, QMessageBox, QGraphicsColorizeEffect, QApplication
from PyQt5.QtCore import Qt, QTime, QDate, QSortFilterProxyModel
from PyQt5.QtGui import QBrush, QColor, QPixmap
from QT_Files.Hour_Registry_QT import Ui_MainWindow
from QT_Files.Hour_Registry_Settings_QT import Ui_Settings_dialog
from Hour_Registry_Table_Populate import DataFrameModel
from Hour_Registry_SQL import SQL_Database
from Hour_Registry_get_db import Get_db
from Hour_Registry_Settings_dialog_functions import Settings_dialog
from Hour_Registry_PI_dialog_functions import ProjectInput_edit_dialog
from Hour_Registry_TI_dialog_functions import TaskInput_edit_dialog
from Hour_Registry_DH_dialog_functions import DailyHours_edit_dialog
from Hour_Registry_Mpl_Canvas import MplWidget
from Hour_Registry_concatenate_tables import Concatentate_tables
from Qrangeslider import QRangeSlider
from datetime import datetime, date
import pandas as pd

pd.options.mode.chained_assignment = None  # default='warn'

# Just to see the complete dataframe in my terminal on print
pd.set_option('display.width', 500)
pd.set_option('display.max_columns', 10)



# TODO: some error in total plot, when hours worked turn back to 0 (delete) values in plot remain
# Problem arises because divide to 0 is prevented by df["total"] != 0

# TODO: auto oracle name line might be irritating
# Not possible to make into preference: Settings > bound to signal/slot on changed (parent)
# TODO: import projects and task from other db (or just import old one and delete daily db)
# Add menubar Settings option to Local database , select local DB button
# Notification : a copy of the selected db will be added to: path
# ! dangerours ! if db other format > hard to recognize error
# Add menubar option : Delete daily hours
# > Request confirmation
# TODO: Reorder hours option, so that daily maximum is not exceeded
# Add option in Settings (checkbox toggle)
# Add contract hours label, line edit (Integer)
# If contract hours is exceeded, split hours in day with most hours worked, at project with most hours
# Create new line with Toil 1.0 time type
# ! might be to complicated for python to do efficiently !
# TODO: add secondary x axis to Total plot with week numbers
# TODO: expand total plot with Company filter, project filter
# Dropdown: Oracle Task name, taskname, Project, Client
# Harder than expected, Total db is stored as project ID. Hard to distill task/project/ect.
# TODO: tight_layout fix
def update_table(table, df):
    """
    Called from:
    - __init__()
    - DailyHours_changed_date()
    - ProjectInput_button_clicked_add_project
    - ProjectInput_button_clicked_delete_project
    - DailyHours_button_clicked_view_all_daily_data
    - delete_all_projects()
    - delete_all_daily_hours()

    Inherits DataFrameModel class from Hour_Registry_Table_Populate.py
    :param table: QTableView (Project Info, Daily Hours)
    :param df: Panda DataFrame (project, daily)
    :return: Populates the QTableViews
    """
    model = DataFrameModel(df)  # Call DataFrameModel Class from Hour_Registry_Table_Populate.py
    proxymodel = QSortFilterProxyModel()  # Proxy model enable sorting of Columns
    proxymodel.setSourceModel(model)
    proxymodel.setFilterKeyColumn(-1)  # -1 to apply to all Columns
    table.setModel(proxymodel)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # Makes table fit to Qtableview Size


def update_combobox(combo_list, df, column):
    """
    Called from:
    - delete_all_projects
    - ProjectInput_button_clicked_add_project
    - ProjectInput_button_clicked_delete_project

    :param column: defines which dataframe column values are inserted in combobox
    :param combo_list: List of all projects or task combo boxes
    :param df: all dataframes posses ["Project Name or Task Name"] column
    :return: Clears and add all projects currently in the respective Dataframes.
    """
    for i in combo_list:
        i.clear()
        if df.empty:
            pass
        else:
            i.addItems(df[column].values)


def plot_set_kpi(billability_percentage, sum_revenue, label_bil, label_rev):
    color_effect = QGraphicsColorizeEffect()
    if float(billability_percentage) < 50:
        color_effect.setColor(Qt.darkRed)
    if 50 <= float(billability_percentage) <= 70:
        color_effect.setColor(Qt.darkYellow)
    if float(billability_percentage) > 70:
        color_effect.setColor(Qt.darkGreen)

    label_bil.setGraphicsEffect(color_effect)
    label_bil.setText(billability_percentage + "%")
    label = ""

    for i in sum_revenue:
        label = label + i + " "
    label_rev.setText(label)


def messagebox(errortype, text, info):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle("Error: " + errortype)
    msg.setText(text)
    msg.setInformativeText(info)
    msg.exec()
    return None


class MyMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        """
        Called from Hour_Registry_Run.py script.

        :param parent:  1: QMainWindow = Python Library,
                        2: Ui_MainWindow = UI script (Hour_Registry_QT.py)
        1. Setup GUI based on parents
        2. Defines Column names for Project, Daily and Weekly tables
        - Used for Panda and SQL
        - Days in weekly_hours_columns is also separately defined to operate timedelta functions  on these columns.
        3. The name of the database is defined
        - saved in directory same directory as files
        4. Calls populate_widgets() function

        """
        super().__init__(
            parent)  # Parent 1: QMainWindow = Python Library, Parent 2: Ui_MainWindow = UI script (Hour_Registry_QT.py)
        self.setupUi(self)  # Opens the UI window

        # Define Column Headers for Panda DataFrames (pi = Project Input, dh = Daily Hours, wh = Weekly Hours)
        self.project_input_columns = ["Client", "Project_Name", "Project_Number", "Oracle_Name_pi",
                                      "Project_Manager", "Client_Contact", "Additional_information_pi"]
        self.task_input_columns = ["Task_Name", "Task_Number", "Oracle_Name_ti", "Billable", "Hourly_Rate", "Currency",
                                   "Comment_ti"]
        self.daily_hours_columns = ["Date", "Start", "End", "Duration", "Project_Name", "Task_Name", "Comment_dh"]
        self.weekly_hours_columns = ["Project_ID", 'Project_Number', "Task_Number", "Monday", "Tuesday", "Wednesday",
                                     "Thursday", "Friday", "Saturday", "Sunday", "Total"]
        self.total_kpi_columns = ["Year", "Week", "Total", "Billable", "Revenue", "Currency"]
        self.weekly_hours_columns_days = self.weekly_hours_columns[3:10]
        self.char_remove = [" ", "-", "+", "=", "~", "&", "^", "(", ")", "{", "}", ".", "'", "\\", "%", "/"]

        self.country, self.company, self.local_database, self.currency, self.roundup, self.resolution = Settings_dialog.set_settings(self)

        # List of Project combo boxes
        self.combobox_list_projects = [self.comboBox_ProjectInput_project_select,
                                       self.comboBox_TaskInput_project_select,
                                       self.comboBox_DailyHours_project_select]
        self.combobox_list_tasks = [self.comboBox_TaskInput_task_select, self.comboBox_DailyHours_task_select]

        self.WeeklyPlot_widget = MplWidget(self.WeeklyPlot_widget)  # QWidget connection with MplWidget class
        self.TotalPlot_widget = MplWidget(self.TotalPlot_widget)  # QWidget connection with MplWidget class
        self.Range_widget = QRangeSlider(self.RangeSlider_widget)  # QWidget connection with RangeSlider class
        self.Range_widget.show()

        current_date = date.today()
        year, week, day = current_date.isocalendar()
        self.spinBox_WeeklyPlot_year.setValue(year)
        self.spinBox_WeeklyPlot_week.setValue(week)
        self.dateEdit_DailyHours_date_select.setDate(QDate.currentDate())  # Initial Date settings
        self.dateEdit_DailyHours_add.setDate(QDate.currentDate())

        self.populate_widgets()


    def populate_widgets(self):
        """
        Called from __init__ function or close_trigger()
        - When application is opened
        - When data is edited

        1. Retrieves the latest data from:
        - SQL db: projects
        - SQL db: daily_hours

        :return:
        2. Set DateEdit fields to today()
        3. Updates combo boxes and tables
        4. Calls DailyHours_changed_date() functions
        - Populates tableview_DailyHours with just Data of today
        """
        try:
            self.country, self.company, self.local_database, self.currency, self.roundup, self.resolution = Settings_dialog.set_settings(self)
            self.comboBox_TaskInput_currency.setCurrentText(self.currency)
            df_project_input = Get_db.get_project_db(self, self.local_database,
                                                     self.project_input_columns)  # Retrieve DataFrames from SQL databases

            update_table(self.tableView_ProjectInput, df_project_input)  # Populate tables / combo boxes
            update_combobox(self.combobox_list_projects, df_project_input, "Project_Name")

            self.DailyHours_changed_date()
            self.WeeklyHours_button_clicked_this_week()
        except TypeError:
            self.TaskInput_button_clicked_clear_input()


    def close_trigger(self):
        """
        Triggered by pyqtSignal window_closed from CloseEvent in:
        - Hour_Registry_PI_dialog_functions.py
        - Hour_Registry_TI_dialog_functions.py
        - Hour_Registry_DH_dialog_functions.py
        :return:
        Populates widgets in MainWindow with the Edited data
        """
        self.populate_widgets()


    def Settings(self):
        self.Settings_dialog = Settings_dialog()
        self.Settings_dialog.window_closed.connect(self.close_trigger)
        self.Settings_dialog.show()


    # ------------------------------------------------------------------#
    # -----------------------    Project Input   -----------------------#
    # ------------------------------------------------------------------#

    def ProjectInput_changed_internal_toggle(self):
        """
        QCheckbox with a toggle layout
        :return:
        disable or enable LineEdits fields within Project Input
        check or uncheck Billable checkbox
        calls ProjectInput_changed_billable_toggle()
        """
        check = self.checkBox_ProjectInput_internal.isChecked()
        if check:
            self.label_ProjectInput_client.setDisabled(True)
            self.lineEdit_ProjectInput_client.setDisabled(True)
            self.lineEdit_ProjectInput_client_contact.setDisabled(True)
            self.lineEdit_ProjectInput_client.setText(self.company)
            self.label_ProjectInput_client_contact.setDisabled(True)
            self.lineEdit_ProjectInput_client_contact.setDisabled(True)
        else:
            self.label_ProjectInput_client.setDisabled(False)
            self.lineEdit_ProjectInput_client.setDisabled(False)
            self.lineEdit_ProjectInput_client_contact.setDisabled(False)
            self.label_ProjectInput_client_contact.setDisabled(False)
            self.lineEdit_ProjectInput_client_contact.setDisabled(False)

    def ProjectInput_button_clicked_clear_input(self):
        """
        Called from:
        - Clear Input Button
        - Add project button

        :return:
        Clears all LineEdits within Project Input
        """
        ProjectInput_lineEdits = [self.lineEdit_ProjectInput_client, self.lineEdit_ProjectInput_project_name,
                                  self.lineEdit_ProjectInput_project_number,
                                  self.lineEdit_ProjectInput_Oracle_name,
                                  self.lineEdit_ProjectInput_project_manager,
                                  self.lineEdit_ProjectInput_client_contact,
                                  self.lineEdit_ProjectInput_additional_information]
        for items in ProjectInput_lineEdits:
            items.clear()

    def ProjectInput_name_number_changed(self):
        name = self.lineEdit_ProjectInput_project_name.text()
        number = self.lineEdit_ProjectInput_project_number.text()
        oracle_name = number + " - " + name
        self.lineEdit_ProjectInput_Oracle_name.setText(oracle_name)

    def ProjectInput_button_clicked_add_project(self):
        """
        Called from: Add Project Button
        :return:
        1) Reads the input lines and converts it into a single row Dataframe.
        2) This dataframe is joined to the pre-existing Dataframe
        3) SQL database is updated
        4) Gui is updated
        """
        df = Get_db.get_project_db(self, self.local_database, self.project_input_columns)
        valid_project_name = self.lineEdit_ProjectInput_project_name.text()
        if valid_project_name == "":
            errortype = "Missing Mandatory Field"
            text = "Project Name is missing"
            info = "Please fill in te [Project Name] field to add this project"
            messagebox(errortype, text, info)
            return None
        for char in self.char_remove:
            valid_project_name = valid_project_name.replace(char, "_")
        if valid_project_name in df["Project_Name"].values:
            errortype = "Duplicate Project Name"
            text = "Project Name already exists"
            info = "Please use another project name"
            messagebox(errortype, text, info)
            return None
        new_row = [self.lineEdit_ProjectInput_client.text(),
                   valid_project_name,
                   self.lineEdit_ProjectInput_project_number.text(),
                   self.lineEdit_ProjectInput_Oracle_name.text(),
                   self.lineEdit_ProjectInput_project_manager.text(),
                   self.lineEdit_ProjectInput_client_contact.text(),
                   self.lineEdit_ProjectInput_additional_information.text()]
        df_new_row = pd.DataFrame([new_row], columns=self.project_input_columns)
        df_project_input = pd.concat([df, df_new_row])
        df_project_input.reset_index(drop=True, inplace=True)

        # SQL commands
        db = SQL_Database(f"{self.local_database}")
        df_new_row.to_sql('projects', db._conn, if_exists="append", index=False)

        # Update GUI
        update_table(self.tableView_ProjectInput, df_project_input)
        update_combobox(self.combobox_list_projects, df_project_input, "Project_Name")
        self.ProjectInput_button_clicked_clear_input()
        self.ProjectInput_changed_internal_toggle()

    def ProjectInput_button_clicked_delete_project(self):
        """
        :return: Deletes project equal to the project id in the QCombobox
        """
        qm = QMessageBox
        ret = qm.question(self, '',
                          "Are you sure you want delete this project? \n Tasks under this project name will also be deleted. ",
                          qm.Yes | qm.No)
        if ret == qm.Yes:
            delete = self.comboBox_ProjectInput_project_select.currentText()
            parameter = (delete,)
            db = SQL_Database(f"{self.local_database}")
            sql = "DELETE FROM projects WHERE Project_Name = ? "
            db.execute(sql, parameter)
            sql2 = f"""DROP TABLE IF EXISTS {delete} """
            db.execute(sql2)
            db.commit()
            db.close()

            df = Get_db.get_project_db(self, self.local_database, self.project_input_columns)
            update_table(self.tableView_ProjectInput, df)
            update_combobox(self.combobox_list_projects, df, "Project_Name")

    def ProjectInput_changed_search_table(self):
        """
        Input = search bar above table
        - reacts on Change
        - Capital sensitive

        :return:
        Filters Tableview through the search bar above the project tableview
        """
        filter_text = self.lineEdit_ProjectInput_search_table.text()
        df = Get_db.get_project_db(self, self.local_database, self.project_input_columns)
        model = DataFrameModel(df)
        proxymodel = QSortFilterProxyModel()
        proxymodel.setSourceModel(model)
        proxymodel.setFilterFixedString(filter_text)
        proxymodel.setFilterKeyColumn(-1)
        self.tableView_ProjectInput.setModel(proxymodel)
        self.tableView_ProjectInput.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def ProjectInput_button_clicked_open_edit_dialog(self):
        """
        Retrieves the integer of the Project selection
        Opens on Project Input - Edit Project button
        :return:
        shows popup dialog: ProjectInput_edit_dialog
        passes project data
        """
        project_name = self.comboBox_ProjectInput_project_select.currentText()
        if project_name == "":  # Project Name is a mandatory field
            pass
        else:
            self.ProjectInput_edit_dialog = ProjectInput_edit_dialog(project_name, self.local_database,
                                                                     self.project_input_columns)
            self.ProjectInput_edit_dialog.window_closed.connect(self.close_trigger)
            self.ProjectInput_edit_dialog.show()

    # ---------------------------------------------------------------#
    # -----------------------    Task Input   -----------------------#
    # ---------------------------------------------------------------#
    def TaskInput_changed_billable_toggle(self):
        """
        QCheckbox with a toggle layout
        :return:
        disable or enable LineEdit fields within Project Input
        """
        check = self.checkBox_TaskInput_billable.isChecked()
        if check:
            self.label_TaskInput_hourly_rate.setDisabled(False)
            self.lineEdit_TaskInput_hourly_rate.setDisabled(False)
        else:
            self.lineEdit_TaskInput_hourly_rate.setText("0")
            self.label_TaskInput_hourly_rate.setDisabled(True)
            self.lineEdit_TaskInput_hourly_rate.setDisabled(True)

    def TaskInput_combobox_changed_project_select(self):
        project = self.comboBox_TaskInput_project_select.currentText()

        if project == "":
            self.comboBox_TaskInput_task_select.clear()
        else:
            df_p = Get_db.get_project_db(self, self.local_database, self.project_input_columns)
            df_pnum = df_p.loc[df_p["Project_Name"] == project]["Project_Number"].values[0]
            self.label_TaskInput_project_number_description.setText(df_pnum)
            df = Get_db.get_task_db(self, self.local_database, project, self.task_input_columns)

            self.comboBox_TaskInput_task_select.clear()
            self.comboBox_TaskInput_task_select.addItems(df["Task_Name"].values)
            update_table(self.tableView_TaskInput, df)

    def TaskInput_button_clicked_clear_input(self):
        """
        Called from:
        - Clear Input Button
        - Add task button

        :return:
        Clears all LineEdits within task Input
        """
        TaskInput_lineEdits = [self.lineEdit_TaskInput_task_name,
                               self.lineEdit_TaskInput_task_number,
                               self.lineEdit_TaskInput_Oracle_name,
                               self.lineEdit_TaskInput_hourly_rate,
                               self.lineEdit_TaskInput_additional_information]
        for items in TaskInput_lineEdits:
            items.clear()

    def TaskInput_name_number_changed(self):
        name = self.lineEdit_TaskInput_task_name.text()
        number = self.lineEdit_TaskInput_task_number.text()
        oracle_name = number + " - " + name
        self.lineEdit_TaskInput_Oracle_name.setText(oracle_name)

    def TaskInput_button_clicked_add_task(self):
        """
        Called from: Add Project Button
        :return:
        1) Reads the input lines and converts it into a single row Dataframe.
        2) This dataframe is joined to the pre-existing Dataframe
        3) SQL database is updated
        4) Gui is updated
        """
        project_name = self.comboBox_TaskInput_project_select.currentText()
        df = Get_db.get_task_db(self, self.local_database, project_name, self.task_input_columns)
        valid_task_name = self.lineEdit_TaskInput_task_name.text()
        if valid_task_name == "":
            errortype = "Missing Mandatory Field"
            text = "Task Name is missing"
            info = "Please fill in te [Task Name] field to add this Task"
            messagebox(errortype, text, info)
            return None
        for char in self.char_remove:
            valid_task_name = valid_task_name.replace(char, "_")
        if valid_task_name in df["Task_Name"].values:
            errortype = "Duplicate Task Name"
            text = "Task Name already exists"
            info = "Please use another task name"
            messagebox(errortype, text, info)
            return None
        try:
            float(self.lineEdit_TaskInput_hourly_rate.text())
        except ValueError:
            errortype = "Invalid Hourly Rate"
            text = "Only float and integers are valid hourly rates"
            info = "Use . as delimiter"
            messagebox(errortype, text, info)
            return None

        new_row = [valid_task_name,
                   self.lineEdit_TaskInput_task_number.text(),
                   self.lineEdit_TaskInput_Oracle_name.text(),
                   int(self.checkBox_TaskInput_billable.isChecked()),
                   self.lineEdit_TaskInput_hourly_rate.text(),
                   self.comboBox_TaskInput_currency.currentText(),
                   self.lineEdit_TaskInput_additional_information.text()]
        df_new_row = pd.DataFrame([new_row], columns=self.task_input_columns)
        df_task_input = pd.concat([df, df_new_row])
        df_task_input.reset_index(drop=True, inplace=True)

        # SQL commands
        db = SQL_Database(f"{self.local_database}")
        df_new_row.to_sql(f'{project_name}', db._conn, if_exists="append", index=False)
        sql = f"SELECT * FROM {project_name}"
        db.execute(sql)
        db.close()

        # Update GUI
        update_table(self.tableView_TaskInput, df_task_input)
        update_combobox(self.combobox_list_tasks, df_task_input, "Task_Name")
        self.comboBox_DailyHours_project_select.setCurrentText(project_name)
        self.TaskInput_button_clicked_clear_input()
        self.TaskInput_changed_billable_toggle()

    def TaskInput_button_clicked_delete_task(self):
        """
        :return: Deletes task equal to the project id in the QCombobox
        """
        qm = QMessageBox
        ret = qm.question(self, '',
                          "Are you sure you want delete this task? \n Hours worked under this task will not be deleted. ",
                          qm.Yes | qm.No)
        if ret == qm.Yes:
            try:
                delete = self.comboBox_TaskInput_task_select.currentText()
                project = self.comboBox_TaskInput_project_select.currentText()
                parameter = (delete,)
                db = SQL_Database(f"{self.local_database}")
                sql = f"""DELETE FROM '{project}' WHERE Task_Name = ? """
                db.execute(sql, parameter)
                db.commit()
                db.close()

                df = Get_db.get_task_db(self, self.local_database, project, self.task_input_columns)
                update_table(self.tableView_TaskInput, df)
                update_combobox(self.combobox_list_tasks, df, "Task_Name")
            except sqlite3.OperationalError:
                errortype = "SQL error"
                text = "Operational Error"
                info = "No such task found in table"
                messagebox(errortype, text, info)
                return None

    def TaskInput_changed_search_table(self):
        """
        Input = search bar above table
        - reacts on Change
        - Capital sensitive

        :return:
        Filters Tableview through the search bar above the project tableview
        """
        filter_text = self.lineEdit_TaskInput_search_table.text()
        project = self.comboBox_TaskInput_project_select.currentText()
        df = Get_db.get_task_db(self, self.local_database, project, self.task_input_columns)
        model = DataFrameModel(df)
        proxymodel = QSortFilterProxyModel()
        proxymodel.setSourceModel(model)
        proxymodel.setFilterFixedString(filter_text)
        proxymodel.setFilterKeyColumn(-1)
        self.tableView_TaskInput.setModel(proxymodel)
        self.tableView_TaskInput.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def TaskInput_button_clicked_open_edit_dialog(self):
        """
        Retrieves the integer of the Task selection
        Opens on Task Input - Edit Task button
        :return:
        shows popup dialog: TaskInput_edit_dialog
        passes task data
        """
        project_name = self.comboBox_TaskInput_project_select.currentText()
        task_name = self.comboBox_TaskInput_task_select.currentText()
        if project_name == "" or task_name == "":
            pass
        else:
            self.TaskInput_edit_dialog = TaskInput_edit_dialog(project_name, task_name, self.local_database,
                                                               self.project_input_columns, self.task_input_columns)
            self.TaskInput_edit_dialog.window_closed.connect(self.close_trigger)
            self.TaskInput_edit_dialog.show()

    # ----------------------------------------------------------------#
    # -----------------------    Daily Hours   -----------------------#
    # ----------------------------------------------------------------#
    def DailyHours_button_clicked_date(self):
        """
        Populates Date dateEdit with current date
        :return:
        """
        date_now = QDate.currentDate()
        self.dateEdit_DailyHours_add.setDate(date_now)
        self.dateEdit_DailyHours_date_select.setDate(date_now)
        self.DailyHours_changed_date()

    def DailyHours_button_clicked_start_time(self):
        """
        Populates Start timeEdit with current time
        :return:
        """
        start_now = QTime.currentTime()
        self.timeEdit_DailyHours_start_time.setTime(start_now)

    def DailyHours_button_clicked_continue_time(self):
        """
        Populates Start timeEdit with the latest end timme of selected day.
        :return:
        """
        date_selected = self.dateEdit_DailyHours_add.date().toString(Qt.ISODate)
        df = Get_db.get_daily_day_db(self, self.local_database, date_selected, self.daily_hours_columns)
        if df.empty:
            continue_time = QTime(00, 00)
        else:
            continue_time = QTime.fromString(df["End"].max(), "hh:mm")
        self.timeEdit_DailyHours_start_time.setTime(continue_time)

    def DailyHours_button_clicked_end_time(self):
        """
        Populates End timeEdit with current time
        :return:
        """
        end_now = QTime.currentTime()
        self.timeEdit_DailyHours_end_time.setTime(end_now)

    def DailyHours_calculate_duration(self):
        """
        Read Start and End timeEdits
        Calculates duration with datetime
        :return:
        Populates duration label with duration in string format
        """
        start_time = self.timeEdit_DailyHours_start_time.time().toString("hh:mm")
        end_time = self.timeEdit_DailyHours_end_time.time().toString("hh:mm")
        time_format = '%H:%M'
        duration = str(datetime.strptime(end_time, time_format) - datetime.strptime(start_time, time_format))
        invalid_duration = duration.startswith("-")
        if invalid_duration:
            raise ValueError
        else:
            self.label_DailyHours_duration_time.setText(duration)

    def DailyHours_combobox_changed_project_select(self):
        project = self.comboBox_DailyHours_project_select.currentText()
        if project == "":
            pass
        else:
            df = Get_db.get_task_db(self, self.local_database, project, self.task_input_columns)
            self.comboBox_DailyHours_task_select.clear()
            self.comboBox_DailyHours_task_select.addItems(df["Task_Name"].values)

    def DailyHours_button_clicked_add_to_table(self):
        """
        :return:
        1) Reads the input lines and converts it into a single row Dataframe.
        2) This dataframe is joined to the pre-existing Dataframe
        3) SQL database is updated
        4) Gui is updated
        """
        try:
            self.DailyHours_calculate_duration()
        except ValueError:
            errortype = "Negative Duration"
            text = "Duration Time cannot be negative"
            info = "Please correct the start or end time"
            messagebox(errortype, text, info)
            return None
        if self.comboBox_DailyHours_project_select.currentText() == "" or self.comboBox_DailyHours_task_select.currentText() == "":
            errortype = "Missing Input"
            text = "No project and/or task was selected."
            info = "Please select a project and/or task to add worked hours."
            messagebox(errortype, text, info)
            return None
        df = Get_db.get_daily_db(self, self.local_database, self.daily_hours_columns)
        new_row = [self.dateEdit_DailyHours_add.date().toString(Qt.ISODate),
                   self.timeEdit_DailyHours_start_time.time().toString("hh:mm"),
                   self.timeEdit_DailyHours_end_time.time().toString("hh:mm"),
                   self.label_DailyHours_duration_time.text(),
                   self.comboBox_DailyHours_project_select.currentText(),
                   self.comboBox_DailyHours_task_select.currentText(),
                   self.lineEdit_DailyHours_additional_information.text()]
        #df_p.loc[df_p["Project_Name"] == project, "Oracle_Name_pi"].iloc[0],
        #df_t.loc[df_t["Task_Name"] == task, "Oracle_Name_ti"].iloc[0],
        df_new_row = pd.DataFrame([new_row], columns=self.daily_hours_columns)
        df_daily_hours = pd.concat([df, df_new_row])
        df_daily_hours.reset_index(drop=True, inplace=True)
        db = SQL_Database(f"{self.local_database}")
        df_new_row.to_sql('daily', db._conn, if_exists="append", index=False)

        self.dateEdit_DailyHours_date_select.setDate(self.dateEdit_DailyHours_add.date())
        self.DailyHours_changed_date()
        self.lineEdit_DailyHours_additional_information.clear()

    def DailyHours_changed_date(self):
        """
        Called from:
        - populate_widget()
        - DailyHours_button_clicked_date
        - DailyHours_button_clicked_add_to_table()
        - DailyHours_button_clicked_remove_time_interval

        :return:
        1. Populates Daily Hours tableview with values of the changed date.
        2. Populates the time select combobox with all time intervals of the changed date.
        """
        date_filter = self.dateEdit_DailyHours_date_select.date().toString(Qt.ISODate)
        df = Get_db.get_daily_db(self, self.local_database, self.daily_hours_columns)
        df = df[["Date", "Start", "End", "Duration", "Project_Name", "Task_Name", "Comment_dh"]]
        model = DataFrameModel(df)
        proxymodel = QSortFilterProxyModel()
        proxymodel.setSourceModel(model)
        proxymodel.setFilterFixedString(date_filter)
        proxymodel.setFilterKeyColumn(0)
        self.tableView_DailyHours.setModel(proxymodel)
        self.tableView_DailyHours.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.comboBox_DailyHours_time_select.clear()
        start_filter = df['Start'].loc[df['Date'] == date_filter]
        end_filter = df['End'].loc[df['Date'] == date_filter]
        time_interval = start_filter + "-" + end_filter
        self.comboBox_DailyHours_time_select.addItems(time_interval)
        try:
            if str(time_interval.iloc[-1]) in time_interval.iloc[:-1].values:
                errortype = "Time Interval already exists"
                text = "The exact time interval already exists for this day"
                info = "You can continue, but future edits or delete actions will apply to all identical time intervals."
                messagebox(errortype, text, info)
        except IndexError:
            pass

    def DailyHours_button_clicked_remove_time_interval(self):
        """
        :return: Deletes Daily input equal to the value in the QCombobox
        """
        qm = QMessageBox
        ret = qm.question(self, '',
                          "Are you sure you want delete this time interval?",
                          qm.Yes | qm.No)

        if ret == qm.Yes:
            delete = str(self.comboBox_DailyHours_time_select.currentText())
            if delete == "":
                errortype = "Cannot Delete"
                text = "No time interval was selected to delete."
                info = "Please select a valid time interval to delete."
                messagebox(errortype, text, info)
                return None
            start_del = delete.split("-")[0]
            end_del = delete.split("-")[1]
            date_del = self.dateEdit_DailyHours_date_select.date().toString(Qt.ISODate)
            parameter = (date_del, start_del, end_del,)
            sql = "DELETE FROM daily WHERE Date = ? AND Start = ? AND End = ? "
            db = SQL_Database(f"{self.local_database}")
            db.execute(sql, parameter)
            db.commit()
            db.close()
            self.DailyHours_changed_date()

    def DailyHours_changed_search_table(self):
        """
        Input = search bar above table
        - reacts on Change
        - Capital sensitive

        :return:
        Filters Tableview through the search bar above the daily hours tableview
        """
        filter_text = self.lineEdit_DailyHours_search_table.text()
        df = Get_db.get_daily_db(self, self.local_database, self.daily_hours_columns)
        df = df[["Date", "Start", "End", "Duration", "Project_Name", "Task_Name", "Comment_dh"]]
        model = DataFrameModel(df)
        proxymodel = QSortFilterProxyModel()
        proxymodel.setSourceModel(model)
        proxymodel.setFilterFixedString(filter_text)
        proxymodel.setFilterKeyColumn(-1)
        self.tableView_DailyHours.setModel(proxymodel)
        self.tableView_DailyHours.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def DailyHours_button_clicked_view_all_daily_data(self):
        """
        Enables user to see data without date selected filter.
        :return:
        The tableview Daily Hours table view will show all data, not filtering on date.
        """
        df = Get_db.get_daily_db(self, self.local_database, self.daily_hours_columns)
        df = df[["Date", "Start", "End", "Duration", "Project_Name", "Task_Name", "Comment_dh"]]
        update_table(self.tableView_DailyHours, df)

    def DailyHours_button_clicked_open_edit_dialog(self):
        """
        Reads combo boxes with Date and time interval selected
        Opens on Daily Hours - Edit button
        :return:
        shows popup dialog: DailyHours_edit_dialog
        passes Date and Time interval selection data
        """
        df = Get_db.get_project_db(self, self.local_database, self.project_input_columns)
        interval_selected = str(self.comboBox_DailyHours_time_select.currentText())
        if interval_selected == "":
            errortype = "Cannot edit"
            text = "No time interval was selected to edit."
            info = "Please select a valid time interval to edit."
            messagebox(errortype, text, info)
            return None
        date_selected = self.dateEdit_DailyHours_date_select.date().toString(Qt.ISODate)

        self.DailyHours_edit_dialog = DailyHours_edit_dialog(df["Project_Name"].values, interval_selected,
                                                             date_selected,
                                                             self.local_database, self.daily_hours_columns,
                                                             self.task_input_columns)
        self.DailyHours_edit_dialog.window_closed.connect(self.close_trigger)
        self.DailyHours_edit_dialog.show()

    # -------------------------------------  --------------------------#
    # -----------------------    Weekly Hours   -----------------------#
    # -------------------------------------  --------------------------#
    def WeeklyHours_button_clicked_this_week(self):
        """
        Sets the year, week to the current Week
        :return:
        Calls
        - WeeklyHours_changed_calender()
        - WeeklyHours_changed_week()
        """

        current_date = date.today()
        year, week_num, day_of_week = current_date.isocalendar()  # Using iso calendar() function
        self.calendarWidget_WeeklyHours.setSelectedDate(date.fromisocalendar(year, week_num, day_of_week))
        self.WeeklyHours_changed_calender()

    def WeeklyHours_button_clicked_export(self):
        filename = QFileDialog.getSaveFileName(self, 'Select File', filter='*.xlsx')
        if filename[0] == '':
            pass
        else:
            try:
                if self.roundup == "true":
                    resolution_dict = {0: 0.1, 1: 0.2, 2: 0.25}
                    resolution = (resolution_dict[self.resolution])
                    self.df_final_export[['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']] = \
                        self.df_final_export[['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']].div(resolution).round().mul(resolution)

                self.df_final_export.to_excel(filename[0], index=False, engine='openpyxl')
            except PermissionError:
                errortype = "Cannot Write to Excel"
                text = "Permission Error"
                info = "You might have this file already opened"
                messagebox(errortype, text, info)
                return None

    def WeeklyHours_changed_calender(self):
        """
        The calendar is an interactive widget
        :return:
        Calls
        - WeeklyHours_button_clicked_this_week()
        - WeeklyHours_changed_week()
        """
        cal_date = self.calendarWidget_WeeklyHours.selectedDate()
        week, year = cal_date.weekNumber()
        week_it = [1, 2, 3, 4, 5, 6, 7]
        labels = self.label_WeeklyHours_monday_date, self.label_WeeklyHours_tuesday_date, \
                 self.label_WeeklyHours_wednesday_date, self.label_WeeklyHours_thursday_date, \
                 self.label_WeeklyHours_friday_date, self.label_WeeklyHours_saturday_date, \
                 self.label_WeeklyHours_sunday_date

        date_days = []
        for day_num, label in zip(week_it, labels):
            day = date.fromisocalendar(year, week, day_num)
            label.setText(str(day))
            date_days.append(day)

        date_days = [str(i) for i in date_days]
        self.WeeklyHours_concatenate_daily_sum_db(date_days, year, week)

    def WeeklyPlot_spinboxes_changed(self):
        """
        This function is called from
        - WeeklyHours_button_clicked_this_week()
        or
        - WeeklyHours_changed_calendar

        Concatenates Year, Week and Day
        :return:
        Sets Date labels above WeeklyHours tableview

        Calls WeeklyHours_concatenate_daily_sum_db

        """
        year = self.spinBox_WeeklyPlot_year.value()

        week = self.spinBox_WeeklyPlot_week.value()

        first_day = datetime.strptime(f"{year}-{week}-1", "%Y-%W-%w")

        date_days = pd.date_range(first_day, periods=7).strftime("%Y-%m-%d").to_list()
        try:
            self.WeeklyHours_concatenate_daily_sum_db(date_days, year, week)
        except:
            pass

    def WeeklyHours_concatenate_daily_sum_db(self, date_days, year, week):
        """
        Retrieves export Dataframe, weekly hours Dataframe and KPI
        From Hour_Registry_concatenate_tables.py

        :param date_days: days within week of Weekly Plot
        :param year:
        :param week:
        :return:
        - Sets labels and KPI in Weekly Hours tab
        - Sets Dataframe in Weekly Hours Tab

        - Adds weekly table to total SQL db
        - Plots Weekly data
        """
        df_final_export, weekly_hours, total_db, billability_percentage, sum_revenue_cur, weekly_worked_hours = \
            Concatentate_tables.concatenate_daily_sum_db(self, date_days, year, week)
        self.df_final_export = df_final_export
        self.label_WeeklyHours_sum_total.setText(weekly_worked_hours)

        # Sends weekly hours DF to DataFrameModel class to populate Weekly Hours tableview
        model = DataFrameModel(weekly_hours)
        self.tableView_WeeklyHours.setModel(model)
        # Resize DF to fit Tableview
        self.tableView_WeeklyHours.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Populates Labels
        self.WeeklyHours_sum_labels(weekly_hours[self.weekly_hours_columns_days], model)

        self.Total_add_to_table(total_db, year, week)
        if sum(total_db["Total"]) != 0:
            MplWidget.WeeklyPlot(self, weekly_hours, year, week)
            plot_set_kpi(billability_percentage, sum_revenue_cur, self.label_WeeklyPlot_billability_indicator,
                         self.label_WeeklyPlot_revenue_indicator)

    def WeeklyHours_sum_labels(self, weekly_hours, model):
        """
        Called from : WeeklyHours_concatenate_daily_sum_db()
        > In turn called from WeeklyHours_changed_week()

        :param model: Refers to the Qtableview with the Dataframe data
        :param weekly_hours: DF with all worked hours, summed per project but not per day

        Iterates over days and labels
        :return: Sums hours worked per day, and populates corresponding label.
        """
        week_it = [0, 1, 2, 3, 4, 5, 6]
        week_sum = []
        sum_labels = self.label_WeeklyHours_sum_monday, self.label_WeeklyHours_sum_tuesday, \
                     self.label_WeeklyHours_sum_wednesday, self.label_WeeklyHours_sum_thursday, \
                     self.label_WeeklyHours_sum_friday, self.label_WeeklyHours_sum_saturday, \
                     self.label_WeeklyHours_sum_sunday
        for day_num, label in zip(week_it, sum_labels):
            day = round(weekly_hours[self.weekly_hours_columns_days].iloc[:, day_num].sum(), 2)
            week_sum.append(day)
            label.setText(str(day))

        # Styles the Tableview, so that columns match the labels.
        for i in range(len(weekly_hours)):
            model.change_color(i, 0, QBrush(QColor(206, 232, 255)))
            model.change_color(i, 1, QBrush(QColor(206, 232, 255)))
            model.change_color(i, 2, QBrush(QColor(206, 232, 255)))
            model.change_color(i, 8, QBrush(QColor(255, 144, 144)))
            model.change_color(i, 9, QBrush(QColor(255, 144, 144)))
            model.change_color(i, 10, QBrush(QColor(206, 232, 255)))

    def Total_add_to_table(self, total_db, year, week):
        """
        Called from WeeklyHours_concatenate_daily_sum_db
        > In turn Called from Weekly_hours_changed_week()

        renames Total column to corresponding year and week.

        :param total_db:
        :param year:
        :param week:
        :return:
        If column exists = replace
        If column does not exist = append
        """
        total_db = total_db.rename(columns={"Total": f"{year}_{week:02d}"})
        db = SQL_Database(f"{self.local_database}")

        try:
            data = pd.read_sql('SELECT * FROM total', db._conn)
            if total_db.columns.values[-1] in data.columns.values:
                data = data.drop(columns=total_db.columns.values[-1])
            df2 = data.merge(total_db, on=["Project_ID", "Project_Number", "Task_Number"], how="outer")
            df2.to_sql(name='total', con=db._conn, if_exists='replace', index=False)
        except:
            total_db.to_sql(name='total', con=db._conn, if_exists='append', index=False)

    def TotalPlot_button_clicked_refresh(self):

        self.WeeklyHours_button_clicked_this_week()
        groupby = self.combobox_TotalPlot_groupby.currentText()
        groupbydict = {"Project / Task Name": "Project_ID", "Project Number": "Project_Number", "Task Number": "Task_Number"}
        filter_groupby = groupbydict[groupby]

        df_total = Get_db.get_total_db(self, self.local_database)
        df_total = df_total.reindex(sorted(df_total.columns), axis=1)
        df_total = df_total.fillna(float(0.0))

        df_total = df_total.melt(id_vars=["Project_ID", "Project_Number", "Task_Number"], var_name="Date", value_name="Hours")
        year_range = self.spinBox_TotalPlot_year.value()
        week_range = self.Range_widget.getRange()
        start_range = date.fromisocalendar(year_range, week_range[0], 1)
        end_range = date.fromisocalendar(year_range, week_range[1], 6)

        df_total["Date"] = df_total["Date"].astype(str) + "_6"
        df_total["Date"] = pd.to_datetime(df_total["Date"], format="%Y_%W_%w")
        df_total = df_total[(df_total['Date'] > f'{start_range}') & (df_total['Date'] < f'{end_range}')]
        df_total_plot = df_total[df_total["Hours"] != 0]
        df_total_plot = df_total_plot.groupby([filter_groupby, "Date"]).Hours.sum().reset_index()
        df_total_plot = df_total_plot.rename(columns = {filter_groupby: "Project_ID"})

        df_total_kpi = Get_db.get_total_kpi_db(self, self.local_database, self.total_kpi_columns)
        df_total_kpi["Date"] = df_total_kpi["Year"] + "_" + df_total_kpi["Week"] + "_6"
        df_total_kpi["Date"] = pd.to_datetime(df_total_kpi["Date"], format="%Y_%W_%w")
        df_total_kpi = df_total_kpi[(df_total_kpi['Date'] > f'{start_range}') & (df_total_kpi['Date'] < f'{end_range}')]

        if sum(df_total_kpi["Total"].astype(float)) != 0:
            df_total_kpi["Billable_hours"] = df_total_kpi["Total"].astype(float) * (
                df_total_kpi["Billable"].astype(float))
            average_billability = round(sum(df_total_kpi["Billable_hours"]) / sum(df_total_kpi["Total"].astype(float)),
                                        2)

            sum_revenue = df_total_kpi.groupby(["Currency"]).Revenue.sum().reset_index()
            sum_revenue = round(sum_revenue["Revenue"], 2).astype(str) + " " + sum_revenue["Currency"]
            plot_set_kpi(str(average_billability), sum_revenue, self.label_TotalPlot_billability_indicator,
                         self.label_TotalPlot_revenue_indicator)


            MplWidget.TotalPlot(self, df_total_plot, df_total_kpi)

    # -------------------------------------  -----------------------#
    # -----------------------    Menu Bar    -----------------------#
    # -------------------------------------  -----------------------#
    def Export_Daily_database(self):
        df = Get_db.get_daily_db(self, self.local_database, self.daily_hours_columns)
        filename = QFileDialog.getSaveFileName(self, 'Select File', filter='*.xlsx')
        if filename[0] == '':
            pass
        else:
            try:
                df.to_excel(filename[0], index=False, engine='openpyxl')
            except PermissionError:
                errortype = "Cannot Write to Excel"
                text = "Permission Error"
                info = "You might have this file already opened"
                messagebox(errortype, text, info)
                return None


    def Export_Total_database(self):
        df = Get_db.get_total_db(self, self.local_database)
        filename = QFileDialog.getSaveFileName(self, 'Select File', filter='*.xlsx')
        if filename[0] == '':
            pass
        else:
            try:
                df.to_excel(filename[0], index=False, engine='openpyxl')
            except PermissionError:
                errortype = "Cannot Write to Excel"
                text = "Permission Error"
                info = "You might have this file already opened"
                messagebox(errortype, text, info)
                return None


    def aboutQT(self):
        msg = QApplication.aboutQt()


    def aboutProgram(self):
        title = "About this Program"

        text = """\
                    <html>
                    <p>
                    The Hour Registry tool has been designed to keep track of personal hours worked on projects and tasks. <br>
                    It provides certain personal insights such as weekly and overall billability and gained revenue. <br>
                    <br>
                    The Oracle Export combined with the Oracle Time Card Template Tool allows considerable automation of your weekly timecard submission. <br>
                    For a detailed instruction check out the instruction video, which can be accessed through the Oracle Time Card Template. <br>
    
                    <br>
                    The Program is a Python based GUI developed with PyQT. <br>
                    Input is stored in a Sql3lite database and is generally handled with pandas. <br>
                    If you encounter any errors, or if you have questions, suggestions, comments or feedback. <br>
                    <b>Please contact:</b><br>
                    Bart Stam - Arcadis Germany GmbH <br>
                    <a href='%s'>bart.stam@arcadis.com</a> <br>
                    <br>
                    <b>Version Info</b><br>
                    Version: 1.2 <br>
                    Released: April 2023 
                    </p>
                    </html>
                    """ \
               % "mailto: bart.stam@arcadis.com"

        msg = QMessageBox()
        msg.setIconPixmap(QPixmap(":/images/Arcadis_logo.ico"))
        msg.setWindowTitle(title)
        msg.setText(text)

        msg.exec()

        #msg.about(self, title, text)




    def HowToUse(self):
        title = "How does this program work?"

        text = """\
                    <html>
                    <p>
                    <b>1: First click on the menubar "Settings" > "Open Settings". </b><br>
                    Modify the country, company and local database name as desired.<br>
                    The copy to an external (online) database is not yet available in this version.<br>
                    The local database can be found in the installation directory.<br>
                    <br><br>
                    <b>2: Provide a Project and Task dictionary.</b><br>
                    In the <u>Project Input</u> tab you can define new projects.<br>
                    The "Project Name" input, creates a new SQL table.<br>
                    Subsequently, you can add Tasks to the associated project in the <u>Task Input</u> tab.<br>
                    Special Characters within "Project Name" and "Task Name" input are replaced by underscores to enable SQL handling.<br>
                    Also be aware that the "Project Name" and "Task Name" input cannot be edited at a later stage.<br>
                    The Oracle name is automatically generated, for a smooth transition into the Oracle time card template. <br>
                    Please make sure, that the Oracle names are written exactly te same. <br>
                    <br>
                    <b>3: Update your working hours throughout the day. </b><br>
                    Head over to the <u>Daily Hours</u> tab (default tab on launch).<br>
                    You can select the Project and associated Task with the upper dropdowns.<br>
                    Next provide the date, start time, end time and comment (comment is not mandatory). <br>
                    The task comment is transferred to the "All Days" comment, <br>
                    while all daily comments are concatenated and used as "Daily comment". <br>
                    You can do this by editing the yellow boxes, or by clicking the light-blue boxes above.<br>
                    Date = set to current date.<br>
                    Start = set start time to now.<br>
                    Continue = set start time to last end time of selected day.<br>
                    End = set end time to now.<br>
                    Finally click "Add to Table" and you work will appear in the table below.<br>
                    To review, edit or delete time intervals use the yellow date and interval selector below.<br>
                    <br><br>
                    <b>4: Review and Export your Weekly Hours. </b><br>
                    Within the <u> Weekly Hours </u> tab, you can review each week by clicking on dates in the Calendar widget.<br>
                    In the left lower corner you can make an "Oracle Export" excel file for the selected week.<br>
                    A detailed instruction how to use the Time Card Template tool is provided within the Oracle Template.<br>
                    <br><br>
                    <b> Additional Features </b><br>
                    In the <u> Weekly Plot </u> and <Total Plot </u> tabs you find a visual representation of you weekly and total worked hours.<br>
                    Additionally, you can find your Billability percentage and revenue gained in the upper boxes.<br>
                    The <u> Total Plot </u> is generated upon the "Refresh" button.<br>
                    In the menu bar <u> Export </u> you can export some SQL tables to an Excel.<br>
                    "Daily Database" exports all inputs which you have ever given in the <u>Daily Hours</u> tab.<br>
                    You can also view this data by clicking "View All Daily Data".<br>
                    "Total Database" provides the cumulative weekly hours per project-task.<br>
                    "Oracle Week Export" is identical to the <u>Weekly Hours</u> "Oracle Export".<br>
                    <br>
                    <b> For any outstanding questions, recommendations or comments, contact: </b> <br>
                     <a href='%s'>bart.stam@arcadis.com</a> <br>
                    </p>
                    </html>
                    """ \
                    % "mailto: bart.stam@arcadis.com"

        msg = QMessageBox.about(self, title, text)

    def DeleteDailyHours(self):
        qm = QMessageBox
        ret = qm.question(self, '', "Are you sure to reset the hours worked databases? \n (Project and Task database are not deleted)", qm.Yes | qm.No)

        if ret == qm.Yes:
            db = SQL_Database(f"{self.local_database}")
            sql = "DROP TABLE IF EXISTS total_kpi;"
            db.execute(sql)
            sql2 = "DROP TABLE IF EXISTS total;"
            db.execute(sql2)
            sql3 = "DROP TABLE IF EXISTS daily;"
            db.execute(sql3)
            db.commit()
            db.close()

