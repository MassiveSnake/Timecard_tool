from PyQt5.QtWidgets import QMainWindow, QHeaderView
from PyQt5.QtCore import Qt, QTime, QDate, QSortFilterProxyModel
from PyQt5.QtGui import QBrush, QColor
from QT_Files.Hour_Registry_QT import Ui_MainWindow
from Hour_Registry_Table_Populate import DataFrameModel
from Hour_Registry_SQL import SQL_Database
from Hour_Registry_get_db import Get_db
from Hour_Registry_PI_dialog_functions import ProjectInput_edit_dialog
from Hour_Registry_DH_dialog_functions import DailyHours_edit_dialog


import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
from datetime import datetime, date, timedelta


# Just to see the complete dataframe in my terminal on print
pd.set_option('display.width', 500)
pd.set_option('display.max_columns',10)

#TODO: From weekly to complete database

#TODO: Create CSS dark mode
#sum week,
#Change column name > provide year/week identifiers > single column name with time worked values
#Merge weeks > Groupedby "Project_ID" > Sort on week number
#TODO: On plots tab, create: REFRESH DATA button. > gathers all weekly databases, create single week sorted db (also reverse sortable)
#TODO: Message box for - If record is edited, - Confirmation if menubar option delete
#TODO: Add combobox to daily hours - where user can add/choose a reoccuring description for each project



class MyMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        """
        Called from Hour_Registry_Run.py script.

        :param parent:  1: QMainWindow = Python Library,
                        2: Ui_MainWindow = UI script (Hour_Registry_QT.py)
        1. Setup GUI based on parents
        2. Defines Column names for Project, Daily and Weekly tables
        - Used for Panda and SQL
        - Days in weekly_hours_columns is alse seperately defined to operate timedelta functions  on these columns.
        3. The name of the database is defined
        - saved in directory same directory as files
        4. Calls populate_widgets() function

        """
        #TODO: Where do we want to save our Database?
        super().__init__(parent) #Parent 1: QMainWindow = Python Library, Parent 2: Ui_MainWindow = UI script (Hour_Registry_QT.py)
        self.setupUi(self) # Opens the UI window

        # Define Column Headers for Panda DataFrames (pi = Project Input, dh = Daily Hours, wh = Weekly Hours)
        self.project_input_columns = ["Project_ID", "Client", "Project_Name", "Project_Number", "Task_Number", "Hourly_Rate", "Currency",
                        "Project_Manager", "Client_Contact", "Additional_information_pi"]
        self.daily_hours_columns = ["Date", "Start", "End", "Duration", "Project_ID", "Additional_information_dh"]
        self.weekly_hours_columns = ["Project_ID", 'Project_Number', "Task_Number", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Total"]
        self.weekly_hours_columns_days = self.weekly_hours_columns[3:10]

        # List of Project comboboxes
        self.combobox_list_projects = [self.comboBox_ProjectInput_project_select,
                              self.comboBox_DailyHours_project_select]

        self.hour_database = "Hour_Database_BFS.db"
        self.populate_widgets()

    def populate_widgets(self):
        """
        Called from __init__ function or close_trigger()
        - When application is opened
        - When data is edited

        1. Retrieves latest data from:
        - SQL db: projects
        - SQL db: daily_hours

        :return:
        2. Set DateEdit fields to today()
        3. Updates comboboxes and tables
        4. Calls DailyHours_changed_date() functions
        - Populates tableview_DailyHours with just Data of today
        """
        # Retrieve DataFrames from SQL databases
        df_project_input = Get_db.get_project_db(self, self.project_input_columns )

        # Initial Date settings
        self.dateEdit_DailyHours_date_select.setDate(QDate.currentDate())
        self.dateEdit_DailyHours_add.setDate(QDate.currentDate())

        # Populate tables / comboboxes
        self.update_table(self.tableView_ProjectInput, df_project_input)
        self.update_combobox(self.combobox_list_projects, df_project_input)
        self.DailyHours_changed_date()

    def close_trigger(self):
        """
        Triggered by pyqtSignal window_closed from CloseEvent in:
        - Hour_Registry_PI_dialog_functions.py
        - Hour_Registry_DH_dialog_functions.py
        :return:
        Populates widgets in MainWindow with the Edited data
        """
        self.populate_widgets()


    def ProjectInput_button_clicked_open_edit_dialog(self):
        """
        Retrieves the integer of the Project selction (project ID)
        Opens on Project Input - Edit Project button
        :return:
        shows popup dialog: ProjectInput_edit_dialog
        passes project id data
        """
        project_id = self.comboBox_ProjectInput_project_select.currentText().split("-")[0]
        self.ProjectInput_edit_dialog = ProjectInput_edit_dialog(project_id, self.hour_database, self.project_input_columns)
        self.ProjectInput_edit_dialog.window_closed.connect(self.close_trigger)
        self.ProjectInput_edit_dialog.show()

    def DailyHours_button_clicked_open_edit_dialog(self):
        """
        Reads comboboxes with Date and time interval selected
        Opens on Daily Hours - Edit button
        :return:
        shows popup dialog: DailyHours_edit_dialog
        passes Date and Time interval selection data
        """
        df = Get_db.get_project_db(self, self.project_input_columns)
        interval = str(self.comboBox_DailyHours_time_select.currentText())
        date = self.dateEdit_DailyHours_date_select.date().toString(Qt.ISODate)

        self.DailyHours_edit_dialog = DailyHours_edit_dialog(df["Project_ID"].values, interval, date, self.hour_database, self.daily_hours_columns)
        self.DailyHours_edit_dialog.window_closed.connect(self.close_trigger)
        self.DailyHours_edit_dialog.show()

    def update_table(self, table,  df):
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
        model = DataFrameModel(df) # Call DataFrameModel Class from Hour_Registry_Table_Populate.py
        proxymodel = QSortFilterProxyModel() # Proxymodel enable sorting of Columns
        proxymodel.setSourceModel(model)
        proxymodel.setFilterKeyColumn(-1) # -1 to apply to all Columns
        table.setModel(proxymodel)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)


    def update_combobox(self, combo_list, df):
        """
        Called from:
        - delete_all_projects
        - ProjectInput_button_clicked_add_project
        - ProjectInput_button_clicked_delete_project

        :param combo_list: List of all Project_ID comboboxes
        :param df: all dataframes posses ["Project_ID"] column
        :return: Clears and add all projects currently in the respective Dataframes.
        """
        for i in combo_list:
            i.clear()
            i.addItems(df["Project_ID"].values)

    #-----------------------    Menu bar functions   -----------------------#

    def delete_all_projects(self):
        """
        Trigger: Menubar option
        :return: clears projects Database and updates table and comboboxes.
        """
        sql = ("DELETE FROM projects")
        db = SQL_Database(f"{self.hour_database}")
        db.execute(sql)
        db.close()

        df = Get_db.get_project_db(self, self.cols_pi )
        self.update_table(self.tableView_ProjectInput, df)
        self.update_combobox(self.combobox_list_projects, df)

    def delete_all_daily_hours(self):
        """
        Trigger: Menubar option
        :return: clears daily Database and updates table
        """
        sql = ("DELETE FROM daily")
        db = SQL_Database(f"{self.hour_database}")
        db.execute(sql)
        db.close()

        df = Get_db.get_daily_db(self, self.daily_hours_columns)
        self.update_table(self.tableView_DailyHours, df)

    # -----------------------    Project Input   -----------------------#
    def ProjectInput_changed_internal_toggle(self):
        """
        QCheckbox with a toggle layout
        :return:
        disable or enable LineEdits fields within Project Input
        check or uncheck Billible checkbox
        calls ProjectInput_changed_billable_toggle()
        """
        check = self.checkBox_ProjectInput_internal.isChecked()
        if check == True:
            self.label_ProjectInput_client.setDisabled(True)
            self.lineEdit_ProjectInput_client.setDisabled(True)
            self.lineEdit_ProjectInput_client_contact.setDisabled(True)
            self.lineEdit_ProjectInput_client.setText("Arcadis")
            self.lineEdit_ProjectInput_hourly_rate.setText("0")
            self.checkBox_ProjectInput_billable.setChecked(False)
            self.label_ProjectInput_client_contact.setDisabled(True)
            self.lineEdit_ProjectInput_client_contact.setDisabled(True)
        else:
            self.label_ProjectInput_client.setDisabled(False)
            self.lineEdit_ProjectInput_client.setDisabled(False)
            self.lineEdit_ProjectInput_client_contact.setDisabled(False)
            self.checkBox_ProjectInput_billable.setChecked(True)
            self.label_ProjectInput_client_contact.setDisabled(False)
            self.lineEdit_ProjectInput_client_contact.setDisabled(False)

    def ProjectInput_changed_billable_toggle(self):
        """
        QCheckbox with a toggle layout
        :return:
        disable or enable LineEdit fields within Project Input
        """
        check = self.checkBox_ProjectInput_billable.isChecked()
        if check == True:
            self.label_ProjectInput_hourly_rate.setDisabled(False)
            self.lineEdit_ProjectInput_hourly_rate.setDisabled(False)
            self.comboBox_ProjectInput_currency.setDisabled(False)
        else:
            self.lineEdit_ProjectInput_hourly_rate.setText("0")
            self.label_ProjectInput_hourly_rate.setDisabled(True)
            self.lineEdit_ProjectInput_hourly_rate.setDisabled(True)
            self.comboBox_ProjectInput_currency.setDisabled(True)

    def ProjectInput_button_clicked_clear_input(self):
        """
        Called from:
        - Clear Input Button
        - Add project button

        :return:
        Clears all LineEdits within Project Input
        """
        PI_items = [self.lineEdit_ProjectInput_client,  self.lineEdit_ProjectInput_project_name, self.lineEdit_ProjectInput_project_number,
                    self.lineEdit_ProjectInput_task_number, self.lineEdit_ProjectInput_hourly_rate, self.lineEdit_ProjectInput_project_manager,
                    self.lineEdit_ProjectInput_client_contact, self.lineEdit_ProjectInput_additional_information]
        for items in PI_items:
            items.clear()

    def ProjectInput_button_clicked_add_project(self):
        """
        Called from: Add Project Button
        :return:
        1) Reads the input lines and converts it into a single row Dataframe.
        2) This dataframe is joined to the pre-existing Dataframe
        3) SQL database is updated
        4) Gui is updated
        """
        df = Get_db.get_project_db(self, self.project_input_columns )
        if df.empty:
            new_index = 1
        else:
            index = int(df["Project_ID"].iloc[-1].split("-")[0])
            new_index = index+1

        project_id = (str(str(new_index)+ '-' +self.lineEdit_ProjectInput_client.text()+ '-' + self.lineEdit_ProjectInput_project_name.text()))
        new_row = [project_id,
                   self.lineEdit_ProjectInput_client.text(),
                   self.lineEdit_ProjectInput_project_name.text(),
                   self.lineEdit_ProjectInput_project_number.text(),
                   self.lineEdit_ProjectInput_task_number.text(),
                   self.lineEdit_ProjectInput_hourly_rate.text(),
                   self.comboBox_ProjectInput_currency.currentText(),
                   self.lineEdit_ProjectInput_project_manager.text(),
                   self.lineEdit_ProjectInput_client_contact.text(),
                   self.lineEdit_ProjectInput_additional_information.text()]
        df_new_row = pd.DataFrame([new_row], columns=self.project_input_columns)
        df_project_input = pd.concat([df, df_new_row])
        df_project_input.reset_index(drop=True, inplace=True)

        # SQL commands
        db = SQL_Database(f"{self.hour_database}")
        df_new_row.to_sql('projects', db._conn, if_exists="append", index = False)
        sql = "SELECT * FROM projects"
        db.execute(sql)
        db.close()

        # Update GUI
        self.update_table(self.tableView_ProjectInput,  df_project_input)
        self.update_combobox(self.combobox_list_projects, df_project_input)
        self.ProjectInput_button_clicked_clear_input()

    def ProjectInput_button_clicked_delete_project(self):
        """
        :return: Deletes project equal to the project id in the QCombobox
        """
        delete = self.comboBox_ProjectInput_project_select.currentText()
        parameter = (delete,)
        db = SQL_Database(f"{self.hour_database}")
        sql = "DELETE FROM projects WHERE Project_ID = ? "
        db.execute(sql, parameter)
        db.commit()
        db.close

        df = Get_db.get_project_db(self, self.project_input_columns )
        self.update_table(self.tableView_ProjectInput,  df)
        self.update_combobox(self.combobox_list_projects, df)

    def ProjectInput_changed_search_table(self):
        """
        Input = search bar above table
        - reacts on Change
        - Capital sensitive

        :return:
        Filters Tableview through the search bar above the project tableview
        """
        filter_text = self.lineEdit_ProjectInput_search_table.text()
        df = Get_db.get_project_db(self, self.project_input_columns )
        model = DataFrameModel(df)
        proxymodel = QSortFilterProxyModel()
        proxymodel.setSourceModel(model)
        proxymodel.setFilterFixedString(filter_text)
        proxymodel.setFilterKeyColumn(-1)
        self.tableView_ProjectInput.setModel(proxymodel)
        self.tableView_ProjectInput.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)


    # -----------------------    Daily Hours   -----------------------#
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
        date = self.dateEdit_DailyHours_add.date().toString(Qt.ISODate)
        df = Get_db.get_daily_day_db(self, date, self.daily_hours_columns)
        if df.empty:
            continue_time = QTime(00,00)
        else:
            continue_time = QTime.fromString(df["End"].max(),"hh:mm")
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
        format = '%H:%M'
        duration = str(datetime.strptime(end_time, format) - datetime.strptime(start_time, format))
        self.label_DailyHours_duration_time.setText(duration)

    def DailyHours_button_clicked_add_to_table(self):
        """

        :return:
        1) Reads the input lines and converts it into a single row Dataframe.
        2) This dataframe is joined to the pre-existing Dataframe
        3) SQL database is updated
        4) Gui is updated
        """
        self.DailyHours_calculate_duration()
        df = Get_db.get_daily_db(self, self.daily_hours_columns)

        new_row = [ self.dateEdit_DailyHours_add.date().toString(Qt.ISODate),
                    self.timeEdit_DailyHours_start_time.time().toString("hh:mm"),
                    self.timeEdit_DailyHours_end_time.time().toString("hh:mm"),
                    self.label_DailyHours_duration_time.text(),
                    self.comboBox_DailyHours_project_select.currentText(),
                    self.lineEdit_DailyHours_additional_information.text()]
        df_new_row = pd.DataFrame([new_row], columns=self.daily_hours_columns)
        df_daily_hours = pd.concat([df, df_new_row])
        df_daily_hours.reset_index(drop=True, inplace=True)
        db = SQL_Database(f"{self.hour_database}")
        df_new_row.to_sql('daily', db._conn, if_exists="append", index=False)

        sql = "SELECT * FROM daily"
        db.execute(sql)
        db.close()

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
        df = Get_db.get_daily_db(self, self.daily_hours_columns)
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

    def DailyHours_button_clicked_remove_time_interval(self):
        """
        :return: Deletes Daily input equal to the value in the QCombobox
        """
        delete = str(self.comboBox_DailyHours_time_select.currentText())
        start_del = delete.split("-")[0]
        end_del = delete.split("-")[1]
        date_del = self.dateEdit_DailyHours_date_select.date().toString(Qt.ISODate)
        parameter = (date_del, start_del, end_del,)
        sql = ("DELETE FROM daily WHERE Date = ? AND Start = ? AND End = ? " )
        db = SQL_Database(f"{self.hour_database}")
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
        df = Get_db.get_daily_db(self, self.daily_hours_columns)
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
        df = Get_db.get_daily_db(self, self.daily_hours_columns)
        self.update_table(self.tableView_DailyHours,  df)


    def DailyHours_button_clicked_sum_up_daily_hours(self):
        """
        Reads the date and defines it as id
        Calls DailyHours_calculate_sum_up()
        :return:
        Populates Daily hours tableview with the summed up hours.
        """
        date_id = self.dateEdit_DailyHours_date_select.date().toString(Qt.ISODate)
        sum_day_df = self.DailyHours_calculate_sum_up(date_id)
        sum_day_df_filter = sum_day_df.dropna(subset=["Duration"]) # I've decided to keep the DF intact, keeping all project in there without hours worked.
        sum_day_df_filter = sum_day_df_filter.reset_index(drop=True) # The filtered (only project with worked hours) are send to the TableView
        model = DataFrameModel(sum_day_df_filter)
        self.tableView_DailyHours.setModel(model)
        self.tableView_DailyHours.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def DailyHours_calculate_sum_up(self, date_id):
        """
        Calculates the sum of hours worked per project per day
        :param date_id: input, which day should be summed
        1. Retrieves duration column from the assigned day
        2. converts into timedelta
        3. sums all timedelta back into float
        :return:
        sum_day_df (Project_ID, Project_number + Project_task + summed duration)
        """
        df = Get_db.get_daily_db(self, self.daily_hours_columns)
        day_df = df[df['Date'] == date_id]
        day_df['Duration'] = pd.to_timedelta(day_df['Duration'])

        df_pt_num = Get_db.get_project_db(self, self.project_input_columns)
        df_pt_num = df_pt_num[["Project_ID", "Project_Number", "Task_Number"]]

        grouped_day_df = day_df.groupby(["Project_ID"])['Duration'].sum().reset_index()
        total_seconds = grouped_day_df["Duration"].dt.total_seconds()
        seconds_in_hour = 60 * 60
        grouped_day_df["Duration"] = round((total_seconds / seconds_in_hour), 2)
        sum_day_df = grouped_day_df.merge(df_pt_num, on="Project_ID", how="outer")

        return sum_day_df

    # -----------------------    Weekly Hours   -----------------------#
    def WeeklyHours_button_clicked_this_week(self):
        """
        Sets the year, week to the current Week
        :return:
        Calls
        - WeeklyHours_changed_calader()
        - WeeklyHours_changed_week()
        """
        current_date = date.today()
        year, week_num, day_of_week = current_date.isocalendar()  # Using isocalendar() function
        self.spinBox_WeeklyHours_week.setValue(week_num)
        self.spinBox_WeeklyHours_year.setValue(year)
        self.calendarWidget_WeeklyHours.setSelectedDate(date.fromisocalendar(year, week_num, day_of_week))

    def WeeklyHours_changed_calander(self):
        """
        The calander is an interactive widget
        :return:
        Calls
        - WeeklyHours_button_clicked_this_week()
        - WeeklyHours_changed_week()
        """
        date = self.calendarWidget_WeeklyHours.selectedDate()
        week, year = date.weekNumber()
        self.spinBox_WeeklyHours_year.setValue(year)
        self.spinBox_WeeklyHours_week.setValue(week)

    def WeeklyHours_changed_week(self):
        """
        This function is called from
        - WeeklyHours_button_clicked_this_week()
        or
        - WeeklyHours_changed_calander

        Concatenates Year, Week and Day
        :return:
        Sets Date labels above WeeklyHours tableview

        Calls WeeklyHours_concatenate_daily_sum_db

        """
        year = self.spinBox_WeeklyHours_year.value()
        week = self.spinBox_WeeklyHours_week.value()
        week_it = [1, 2, 3, 4, 5, 6, 7]
        labels = self.label_WeeklyHours_monday_date, self.label_WeeklyHours_tuesday_date, self.label_WeeklyHours_wednesday_date, \
                 self.label_WeeklyHours_thursday_date, self.label_WeeklyHours_friday_date, self.label_WeeklyHours_saturday_date, self.label_WeeklyHours_sunday_date

        date_days = []
        for day_num, label in zip(week_it, labels):
            day = date.fromisocalendar(year, week, day_num)
            label.setText(str(day))
            date_days.append(day)

        date_days = [str(i) for i in date_days]
        self.WeeklyHours_concanate_daily_sum_db(date_days, year, week)

    def WeeklyHours_concanate_daily_sum_db(self, date_days, year, week):
        """
        Called from : WeeklyHours_changed_week()

        :param date_days: The dates "yyyy-mm-dd" of  the selected week
        :param year: Used to name weekly SQL db
        :param week: Used to name weekly SQL db
        :return:
        """
        df = pd.DataFrame() #empty dataframe to start iteration over Days
        # Iterates over date (input) and attaches the day name
        #1 - Sums the hours per project for that day
        #2 - Renames Duration Column to the day name
        #3 - Concats New Column (new day) to DF based on Project_ID, number and task
        for date, day in zip(date_days, self.weekly_hours_columns_days):
            new_col = self.DailyHours_calculate_sum_up(date)
            df_new_row = pd.DataFrame(new_col)
            df_renamed = df_new_row.rename(columns={"Duration":day})
            df = pd.concat([df,df_renamed],join='outer')

        # Sums the hours worked per day per project
        df = df.groupby(["Project_ID", "Project_Number", "Task_Number"]).sum().reset_index()
        # Reorder columns for safety
        weekly_hours = df[["Project_ID", "Project_Number", "Task_Number", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]]

        # Fills data frame with float to use sum.
        fill_na = weekly_hours[self.weekly_hours_columns_days].fillna(float(0.0))
        weekly_hours["Total"] = round(fill_na[self.weekly_hours_columns_days].sum(axis=1),2)
        # If no hours are worked for a project, that project is dropped from the dataframe
        weekly_hours = weekly_hours[weekly_hours["Total"] != 0]
        # Sums all hours worked and populates Total Label
        self.label_WeeklyHours_sum_total.setText(str(round(weekly_hours["Total"].sum(),2)))

        # Defines name for weekly Database and pushes weekly hours DF to SQL
        total_db = weekly_hours[["Project_ID", "Total"]].copy()
        total_db = total_db.rename(columns={"Total":f"{year}.{week:02d}"})

        print(total_db)


        df = Get_db.get_total_db(self)
        print(df)




        # Sends weekly hours DF to DataFrameModel class to populate Weekly Hours tableview
        model = DataFrameModel(weekly_hours)
        self.tableView_WeeklyHours.setModel(model)
        # Resize DF to fit Tableview
        self.tableView_WeeklyHours.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Populates Labels
        self.WeeklyHours_sum_labels(weekly_hours[self.weekly_hours_columns_days])

        # Styles the Tableview, so that columns match the labels.
        for i in range (len(weekly_hours)):
            model.change_color(i, 0, QBrush(QColor(206, 232, 255)))
            model.change_color(i, 1, QBrush(QColor(206, 232, 255)))
            model.change_color(i, 2, QBrush(QColor(206, 232, 255)))
            model.change_color(i, 8, QBrush(QColor(255, 144, 144)))
            model.change_color(i, 9, QBrush(QColor(255, 144, 144)))
            model.change_color(i, 10, QBrush(QColor(206, 232, 255)))

    def WeeklyHours_sum_labels(self,  weekly_hours):
        """
        Called from : WeeklyHours_concanate_daily_sum_db()
        > In turn called from WeeklyHours_changed_week()

        :param weekly_hours: DF with all worked hours, summed per project but not per day

        Iterates over days and labels
        :return: Sums hours worked per day, and populates corresponding label.
        """
        week_it = [0, 1, 2, 3, 4, 5, 6]
        week_sum = []
        sum_labels = self.label_WeeklyHours_sum_monday, self.label_WeeklyHours_sum_tuesday, self.label_WeeklyHours_sum_wednesday, \
                     self.label_WeeklyHours_sum_thursday, self.label_WeeklyHours_sum_friday, self.label_WeeklyHours_sum_saturday, self.label_WeeklyHours_sum_sunday
        for day_num, label in zip(week_it, sum_labels):
            day = round(weekly_hours[self.weekly_hours_columns_days].iloc[:,day_num].sum(),2)
            week_sum.append(day)
            label.setText(str(day))





    def WH_upload_hours_to_database(self):
        # TODO: From weekly to complete database
        # sum week,
        # Change column name > provide year/week identifiers > single column name with time worked values
        # Merge weeks > Groupedby "Project_ID" > Sort on week number

        print("WH uploud hours to database")

    def make_delta(self, entry):
        h, m, s = entry.split(':')
        return timedelta(hours=int(h), minutes=int(m), seconds=int(s))

