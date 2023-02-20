from PyQt5.QtWidgets import QMainWindow, QHeaderView
from PyQt5.QtCore import Qt, QSettings,  QTime, QDate, QSortFilterProxyModel
from Hour_Registry_QT import Ui_MainWindow
from Hour_Registry_Table_Populate import DataFrameModel
from Hour_Registry_SQL import SQL_Database
from Hour_Registry_get_db import Get_db
from Hour_Registry_PI_dialog_functions import PI_dialog
from Hour_Registry_DH_dialog_functions import DH_dialog


import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
from datetime import datetime, date, timedelta
from functools import reduce

pd.set_option('display.width', 500)
pd.set_option('display.max_columns',10)


#TODO: Editing time in daily TableView does not alter duration - might be to complex
#TODO: Make Timedelta / Datetime into class object
#TODO: Implement Timedelta
#TODO: From weekly to complete database
#TODO: make daily hours input editable > combobox in tableview .or. expand deltete line with edit option
#TODO: Create CSS dark mode
#sum week,
#Change column name > provide year/week identifiers > single column name with time worked values
#Merge weeks > Groupedby "Project_ID" > Sort on week number
#TODO: On plots tab, create: REFRESH DATA button. > gathers all weekly databases, create single week sorted db (also reverse sortable)
#TODO: Add billability


class MyMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent) #Parent 1: QMainWindow = Python Library, Parent 2: Ui_MainWindow = UI script (Hour_Registry_QT.py)
        self.setupUi(self) # Opens the UI window

        # Define Column Headers for Panda DataFrames (pi = Project Input, dh = Daily Hours, wh = Weekly Hours)
        self.cols_pi = ["Project_ID", "Client", "Project_Name", "Project_Number", "Task_Number", "Hourly_Rate", "Currency",
                        "Project_Manager", "Client_Contact", "Additional_information_pi"]
        self.cols_dh = ["Date", "Start", "End", "Duration", "Project_ID", "Additional_information_dh"]
        self.cols_dh_sum = ["Project_ID", "Project_Number", "Task_Number", "Duration"]
        self.hour_database = "Hour_Database.db"
        self.populate_widgets()

    def populate_widgets(self):
        # Retrieve DataFrames from SQL databases
        df_pi = Get_db.get_project_db(self, self.cols_pi )
        df_dh = Get_db.get_daily_db(self, self.cols_dh)

        # List of Project comboboxes
        self.combo_list_pi = [self.comboBox_PI_project_del,
                              self.comboBox_DH_project_add]

        # Populate tables / comboboxes on INIT
        self.update_table(self.tableView_PI, df_pi)
        self.update_table(self.tableView_DH, df_dh)
        self.update_combobox(self.combo_list_pi, df_pi)

        # Initial Date settings
        self.dateEdit_DH_remove_time_interval.setDate(QDate.currentDate())
        self.dateEdit_DH.setDate(QDate.currentDate())

    def close_trigger(self):
        self.populate_widgets()


    def PI_open_dialog(self):
        project_id = self.comboBox_PI_project_del.currentText().split("-")[0]
        self.PI_dialog = PI_dialog(project_id, self.hour_database, self.cols_pi)
        self.PI_dialog.window_closed.connect(self.close_trigger)
        self.PI_dialog.show()

    def DH_open_dialog(self):
        df = Get_db.get_project_db(self, self.cols_pi)
        interval = str(self.comboBox_DH_remove_time_interval.currentText())
        date = self.dateEdit_DH_remove_time_interval.date().toString(Qt.ISODate)

        self.DH_dialog = DH_dialog(df["Project_ID"].values, interval, date, self.hour_database, self.cols_dh)
        self.DH_dialog.window_closed.connect(self.close_trigger)
        self.DH_dialog.show()

    def update_table(self, table,  df):
        """
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
        self.update_table(self.tableView_PI, df)
        self.update_combobox(self.combo_list_pi, df)

    def delete_all_daily_hours(self):
        """
        Trigger: Menubar option
        :return: clears daily Database and updates table
        """
        sql = ("DELETE FROM daily")
        db = SQL_Database(f"{self.hour_database}")
        db.execute(sql)
        db.close()

        df = Get_db.get_daily_db(self, self.cols_dh)
        self.update_table(self.tableView_DH, df)

    # -----------------------    Project Input   -----------------------#
    def PI_billable_changed(self):
        check = self.checkBox_billable.isChecked()
        if check == True:
            self.label_PI_rate.setDisabled(False)
            self.lineEdit_PI_rate.setDisabled(False)
            self.comboBox_PI_currency.setDisabled(False)
        else:
            self.lineEdit_PI_rate.setText("0")
            self.label_PI_rate.setDisabled(True)
            self.lineEdit_PI_rate.setDisabled(True)
            self.comboBox_PI_currency.setDisabled(True)

    def PI_internal_changed(self):
        check = self.checkBox_internal.isChecked()
        if check == True:
            self.label_PI_client.setDisabled(True)
            self.lineEdit_PI_client.setDisabled(True)
            self.lineEdit_PI_client_contact.setDisabled(True)
            self.lineEdit_PI_client.setText("Arcadis")
            self.lineEdit_PI_rate.setText("0")
            self.checkBox_billable.setChecked(False)
            self.label_PI_client_contact.setDisabled(True)
            self.lineEdit_PI_client_contact.setDisabled(True)
        else:
            self.label_PI_client.setDisabled(False)
            self.lineEdit_PI_client.setDisabled(False)
            self.lineEdit_PI_client_contact.setDisabled(False)
            self.checkBox_billable.setChecked(True)
            self.label_PI_client_contact.setDisabled(False)
            self.lineEdit_PI_client_contact.setDisabled(False)

    def PI_clear_input(self):
        """
        Trigger: Clear Input Button
        :return:
        """
        PI_items = [self.lineEdit_PI_client,  self.lineEdit_PI_p_name, self.lineEdit_PI_p_number,
                    self.lineEdit_PI_t_number, self.lineEdit_PI_rate, self.lineEdit_PI_p_manager,
                    self.lineEdit_PI_client_contact, self.lineEdit_PI_add_info]
        for items in PI_items:
            items.clear()

    def PI_add_project(self):
        """
        Trigger: Add Project Button
        :return:
        1) Reads the input lines and converts it into a single line Dataframe.
        2) This dataframe is joined to the pre-existing Dataframe
        3) SQL database is updated
        4) Gui is updated
        """
        df = Get_db.get_project_db(self, self.cols_pi )
        if df.empty:
            new_index = 1
        else:
            index = int(df["Project_ID"].iloc[-1].split("-")[0])
            new_index = index+1

        project_id = (str(str(new_index)+ '-' +self.lineEdit_PI_client.text()+ '-' + self.lineEdit_PI_p_name.text()))
        new_row = [project_id,
                   self.lineEdit_PI_client.text(),
                   self.lineEdit_PI_p_name.text(),
                   self.lineEdit_PI_p_number.text(),
                   self.lineEdit_PI_t_number.text(),
                   self.lineEdit_PI_rate.text(),
                   self.comboBox_PI_currency.currentText(),
                   self.lineEdit_PI_p_manager.text(),
                   self.lineEdit_PI_client_contact.text(),
                   self.lineEdit_PI_add_info.text()]
        df_new_row = pd.DataFrame([new_row], columns=self.cols_pi)
        self.df_pi = pd.concat([df, df_new_row])
        self.df_pi.reset_index(drop=True, inplace=True)

        # SQL commands
        db = SQL_Database(f"{self.hour_database}")
        df_new_row.to_sql('projects', db._conn, if_exists="append", index = False)
        sql = "SELECT * FROM projects"
        db.execute(sql)
        db.close()

        # Update GUI
        self.update_table(self.tableView_PI,  self.df_pi)
        self.update_combobox(self.combo_list_pi, self.df_pi)
        self.PI_clear_input()


    def PI_delete_project(self):
        """
        :return: Deletes project equal to the value in the QCombobox
        """
        delete = self.comboBox_PI_project_del.currentText()
        parameter = (delete,)
        db = SQL_Database(f"{self.hour_database}")
        sql = "DELETE FROM projects WHERE Project_ID = ? "
        db.execute(sql, parameter)
        db.commit()
        db.close

        df = Get_db.get_project_db(self, self.cols_pi )
        self.update_table(self.tableView_PI,  df)
        self.update_combobox(self.combo_list_pi, df)

    def PI_search_table_changed(self):
        filter_text = self.lineEdit_PI_search_table.text()
        df = Get_db.get_project_db(self, self.cols_pi )
        model = DataFrameModel(df)
        proxymodel = QSortFilterProxyModel()
        proxymodel.setSourceModel(model)
        proxymodel.setFilterFixedString(filter_text)
        proxymodel.setFilterKeyColumn(-1)
        self.tableView_PI.setModel(proxymodel)
        self.tableView_PI.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)


    # -----------------------    Daily Hours   -----------------------#
    def DH_date_now(self):
        date_now = QDate.currentDate()
        self.dateEdit_DH.setDate(date_now)
        self.dateEdit_DH_remove_time_interval.setDate(date_now)
        self.DH_apply_date_filter()

    def DH_start_now(self):
        start_now = QTime.currentTime()
        self.timeEdit_DH_start.setTime(start_now)

    def DH_end_now(self):
        end_now = QTime.currentTime()
        self.timeEdit_DH_end.setTime(end_now)

    def duration(self):
        self.t_start = self.timeEdit_DH_start.time().toString("hh:mm")
        self.t_end = self.timeEdit_DH_end.time().toString("hh:mm")
        format = '%H:%M'
        duration = str(datetime.strptime(self.t_end, format) - datetime.strptime(self.t_start, format))
        self.label_DH_duration_time.setText(duration)

    def DH_add_to_table(self):
        self.duration()
        df = Get_db.get_daily_db(self, self.cols_dh)

        new_row = [ self.dateEdit_DH.date().toString(Qt.ISODate),
                    self.timeEdit_DH_start.time().toString("hh:mm"),
                    self.timeEdit_DH_end.time().toString("hh:mm"),
                    self.label_DH_duration_time.text(),
                    self.comboBox_DH_project_add.currentText(),
                    self.lineEdit_DH_add_info.text()]
        df_new_row = pd.DataFrame([new_row], columns=self.cols_dh)
        self.df_dh = pd.concat([df, df_new_row])
        self.df_dh.reset_index(drop=True, inplace=True)
        db = SQL_Database(f"{self.hour_database}")
        df_new_row.to_sql('daily', db._conn, if_exists="append", index=False)

        sql = "SELECT * FROM daily"
        db.execute(sql)
        db.close()

        self.dateEdit_DH_remove_time_interval.setDate(self.dateEdit_DH.date())
        self.DH_apply_date_filter()
        self.lineEdit_DH_add_info.clear()

    def DH_apply_date_filter(self):
        date_filter = self.dateEdit_DH_remove_time_interval.date().toString(Qt.ISODate)
        df = Get_db.get_daily_db(self, self.cols_dh)
        model = DataFrameModel(df)
        proxymodel = QSortFilterProxyModel()
        proxymodel.setSourceModel(model)
        proxymodel.setFilterFixedString(date_filter)
        proxymodel.setFilterKeyColumn(0)
        self.tableView_DH.setModel(proxymodel)
        self.tableView_DH.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.comboBox_DH_remove_time_interval.clear()
        start_filter = df['Start'].loc[df['Date'] == date_filter]
        end_filter = df['End'].loc[df['Date'] == date_filter]
        time_interval = start_filter + "-" + end_filter
        self.comboBox_DH_remove_time_interval.addItems(time_interval)

    def DH_remove_time_interval(self):
        """
        :return: Deletes Daily input equal to the value in the QCombobox
        """
        delete = str(self.comboBox_DH_remove_time_interval.currentText())
        start_del = delete.split("-")[0]
        end_del = delete.split("-")[1]
        date_del = self.dateEdit_DH_remove_time_interval.date().toString(Qt.ISODate)
        parameter = (date_del, start_del, end_del,)
        sql = ("DELETE FROM daily WHERE Date = ? AND Start = ? AND End = ? " )
        db = SQL_Database(f"{self.hour_database}")
        db.execute(sql, parameter)
        db.commit()
        db.close()
        self.DH_apply_date_filter()

    def DH_clear_filter(self):
        df = Get_db.get_daily_db(self, self.cols_dh)
        self.update_table(self.tableView_DH,  df)

    def DH_search_table_changed(self):
        filter_text = self.lineEdit_DH_search_table.text()
        df = Get_db.get_daily_db(self, self.cols_dh)
        model = DataFrameModel(df)
        proxymodel = QSortFilterProxyModel()
        proxymodel.setSourceModel(model)
        proxymodel.setFilterFixedString(filter_text)
        proxymodel.setFilterKeyColumn(-1)
        self.tableView_DH.setModel(proxymodel)
        self.tableView_DH.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def DH_sum_date(self):
        date_id = self.dateEdit_DH_remove_time_interval.date().toString(Qt.ISODate)
        sum_day_df = self.DH_sum_up(date_id)
        sum_day_df_filter = sum_day_df.dropna(subset=["Duration"]) # I've decided to keep the DF intact, keeping all project in there without hours worked.
        sum_day_df_filter = sum_day_df_filter.reset_index(drop=True) # The filtered (only project with worked hours) are send to the TableView
        model = DataFrameModel(sum_day_df_filter)
        self.tableView_DH.setModel(model)
        self.tableView_DH.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def DH_sum_up(self, date_id):
        #TODO: make relation to TimeDelta class
        #TODO: remove str[7:15] functionality (convert days to hours instead of split)
        #TODO: WH probaly needs to convert int hours back to timedelta hours
        df = Get_db.get_daily_db(self, self.cols_dh)
        day_df = df[df['Date'] == date_id]
        day_df['Duration'] = pd.to_timedelta(day_df['Duration'])

        df_pt_num = Get_db.get_project_db(self, self.cols_pi )
        df_pt_num = df_pt_num[["Project_ID", "Project_Number", "Task_Number"]]

        grouped_day_df = day_df.groupby(["Project_ID"])['Duration'].sum().reset_index()
        grouped_day_df['Duration'] = grouped_day_df['Duration'].astype(str).str[7:15]
        sum_day_df = grouped_day_df.merge(df_pt_num, on="Project_ID", how="outer")

        #SQL commands
        date_id = date_id.replace("-", "")
        db = SQL_Database(f"{self.hour_database}")
        sum_day_df.to_sql(date_id, db._conn, if_exists="replace", index=False)
        sql = ("SELECT * FROM '" +date_id+ "' ")
        db.execute(sql)
        db.commit()
        db.close()
        return sum_day_df

    # -----------------------    Weekly Hours   -----------------------#
    def WH_this_week(self):
        current_date = date.today()
        year, week_num, day_of_week = current_date.isocalendar()  # Using isocalendar() function
        self.spinBox_WH_week.setValue(week_num)
        self.spinBox_WH_year.setValue(year)
        self.WH_week_changed()

    def WH_calander_changed(self):
        date = self.calendarWidget_WH.selectedDate()
        week, year = date.weekNumber()
        self.spinBox_WH_year.setValue(year)
        self.spinBox_WH_week.setValue(week)

    def WH_week_changed(self):
        year = self.spinBox_WH_year.value()
        week = self.spinBox_WH_week.value()
        week_it = [1, 2, 3, 4, 5, 6, 7]
        labels = self.label_WH_monday_date, self.label_WH_tuesday_date, self.label_WH_wednesday_date, \
                 self.label_WH_thursday_date, self.label_WH_friday_date, self.label_WH_saturday_date, self.label_WH_sunday_date

        date_days = []
        for day_num, label in zip(week_it, labels):
            day = date.fromisocalendar(year, week, day_num)
            label.setText(str(day))
            date_days.append(day)

        self.calendarWidget_WH.setSelectedDate(date_days[0])
        date_days = [str(i) for i in date_days]
        self.WH_grab_daily_sum_db(date_days, year, week)

    def WH_grab_daily_sum_db(self, date_days, year, week):
        for date in date_days:
             self.DH_sum_up(date)
        date_days = [i.replace("-","") for i in  date_days]

        db = SQL_Database(f"{self.hour_database}")
        wh_all = []
        week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        for day, date in zip(week_days, date_days):
            if db.query("SELECT * FROM sqlite_master WHERE type = 'table' AND tbl_name = '" + date + "';"):
                df = pd.read_sql_query("SELECT * FROM '"+date+"'", db._conn)
                df["Project_Number"] = df["Project_Number"].astype(str)
                df["Task_Number"] = df["Task_Number"].astype(str)
                df['Proj-Task #'] = df[['Project_Number', 'Task_Number']].agg(' '.join, axis=1)
                df = df[["Project_ID", 'Proj-Task #', "Duration"]]
                df = df.rename(columns={"Duration" : f"{day}"})

            else:
                df = pd.DataFrame(columns=("Project_ID", 'Proj-Task #' , f"{day}"))
            wh_all.append(df)

        weekly_hours = reduce(lambda x, y: pd.merge(x, y, how="left", on = ['Project_ID','Proj-Task #']), wh_all)


        weekly_hours = weekly_hours[["Project_ID", 'Proj-Task #', "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]]
        self.WH_sum_up(year, week, weekly_hours)


        weekly_db = "Year_" + str(year) + "_Week_" + str(week)
        db = SQL_Database(f"{self.hour_database}")
        weekly_hours.to_sql(weekly_db, db._conn, if_exists="replace", index=False)

        sql = "SELECT * FROM '"+weekly_db+"'"
        db.execute(sql)
        db.close()

        weekly_hours_filter = weekly_hours.dropna(subset=week_days, how='all')
        weekly_hours_filter = weekly_hours_filter.reset_index(drop=True)
        model = DataFrameModel(weekly_hours_filter)
        self.tableView_WH_project.setModel(model)
        self.tableView_WH_project.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.WH_sum_labels(week_days, weekly_hours_filter)

    def WH_sum_labels(self, week_days, weekly_hours_filter):
        sum_day_in_week = weekly_hours_filter.fillna("00:00:00")
        sums = sum_day_in_week[week_days].applymap(lambda entry: self.make_delta(entry))
        week_it = [0, 1, 2, 3, 4, 5, 6]
        week_sum = []
        sum_labels = self.label_WH_sum_monday, self.label_WH_sum_tuesday, self.label_WH_sum_wednesday, \
                     self.label_WH_sum_thursday, self.label_WH_sum_friday, self.label_WH_sum_saturday, self.label_WH_sum_sunday
        for day_num, label in zip(week_it, sum_labels):
            day = sums.iloc[:,day_num].sum()
            week_sum.append(day)
            day = str(day).split('0 days ')[-1]
            label.setText(str(day))

        try:
            week_sum = sum(week_sum, timedelta(0))
            total_seconds = week_sum.total_seconds()
            seconds_in_hour = 60 * 60
            week_sum_in_hours = round((total_seconds / seconds_in_hour),2)
            self.label_WH_sum_total.setText(str(week_sum_in_hours))
        except:
            None

    def WH_sum_up(self, year, week, weekly_hours):
        weekly_proj = weekly_hours[["Project_ID", "Proj-Task #"]]
        weekly_sum = weekly_hours.fillna("00:00:00")
        weekly_sum = weekly_sum[["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]].applymap(lambda entry: self.make_delta(entry))
        weekly_sum[f"sum-{year}-{week}"] = weekly_sum["Monday"] + weekly_sum["Tuesday"] + weekly_sum["Wednesday"]+ weekly_sum["Thursday"]+ weekly_sum["Friday"] + weekly_sum["Saturday"] + weekly_sum["Sunday"]
        weekly_sum = weekly_sum[f"sum-{year}-{week}"]
        df_week =  pd.concat([weekly_proj, weekly_sum], axis=1)
        print(df_week)


    def WH_upload_hours_to_database(self):
        # TODO: From weekly to complete database
        # sum week,
        # Change column name > provide year/week identifiers > single column name with time worked values
        # Merge weeks > Groupedby "Project_ID" > Sort on week number

        print("WH uploud hours to database")

    def make_delta(self, entry):
        h, m, s = entry.split(':')
        return timedelta(hours=int(h), minutes=int(m), seconds=int(s))

