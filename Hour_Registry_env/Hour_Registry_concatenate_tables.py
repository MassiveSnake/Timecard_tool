import pandas as pd
from Hour_Registry_get_db import Get_db
from Hour_Registry_SQL import SQL_Database
from Hour_Registry_Settings_dialog_functions import Settings_dialog
class Concatentate_tables:
    def __init__(self):
        self.project_input_columns = ["Client", "Project_Name", "Project_Number", "Oracle_Name_pi",
                                      "Project_Manager", "Client_Contact", "Additional_information_pi"]
        self.task_input_columns = ["Task_Name", "Task_Number", "Oracle_Name_ti", "Billable", "Hourly_Rate", "Currency", "Comment_ti"]
        self.daily_hours_columns = ["Date", "Start", "End", "Duration", "Project_Name", "Oracle_Name_pi", "Task_Name", "Oracle_Name_ti", "Comment_dh"]
        self.weekly_hours_columns = ["Project_ID", 'Project_Number', "Task_Number", "Monday", "Tuesday", "Wednesday",
                                     "Thursday", "Friday", "Saturday", "Sunday", "Total"]
        self.total_kpi_columns = ["Year", "Week", "Total", "Billable", "Revenue", "Currency"]



    def calculate_sum_up(self, date_id):
        """
        Calculates the sum of hours worked per project per day
        :param date_id: input, which day should be summed
        1. Retrieves duration column from the assigned day
        2. converts into timedelta
        3. sums all timedelta back into float
        :return:
        sum_day_df
        """
        self.country, company, self.local_database, currency, roundup, resolution = Settings_dialog.set_settings(self)
        df = Get_db.get_daily_db(self, self.local_database, self.daily_hours_columns)
        day_df = df[df['Date'] == date_id]
        day_df['Duration'] = pd.to_timedelta(day_df['Duration'])

        grouped_day_df = day_df.groupby(["Project_Name", "Task_Name"])['Duration'].sum().reset_index()

        total_seconds = grouped_day_df["Duration"].dt.total_seconds()
        seconds_in_hour = 60 * 60
        grouped_day_df["Duration"] = round((total_seconds / seconds_in_hour), 2)

        comments_day_df = day_df.groupby(["Date", "Project_Name", "Task_Name"], group_keys=True)["Comment_dh"].apply(lambda x: ','.join(x)).reset_index()
        comment_df = grouped_day_df.merge(comments_day_df, on=["Project_Name", "Task_Name"], how="outer")

        df_p = Get_db.get_project_db(self, self.local_database, self.project_input_columns)

        try:
            concat_df = pd.DataFrame(columns=["Project_Name", "Project_Number", "Task_Name", "Task_Number"])
            for project, pnum, oracle_name_pi in zip(df_p["Project_Name"].values, df_p["Project_Number"].values, df_p["Oracle_Name_pi"].values):
                df_t = Get_db.get_task_db(self, self.local_database, project, self.task_input_columns)
                df_t["Project_Name"] = project
                df_t["Project_Number"]= pnum
                df_t["Oracle_Name_pi"] = oracle_name_pi
                df_t = df_t[["Project_Name",  "Project_Number", "Oracle_Name_pi", "Task_Name", "Task_Number", "Oracle_Name_ti", "Billable", "Hourly_Rate", "Currency", "Comment_ti"]]
                concat_df = pd.concat([concat_df, df_t]).reset_index(drop=True)

            grouped_day_df = grouped_day_df.merge(concat_df, on=["Project_Name", "Task_Name"], how="outer")
            comments_day_df = grouped_day_df.merge(comment_df, on=["Project_Name", "Task_Name", "Duration"], how="outer")

            export_day_df = comments_day_df[["Date", "Project_Name", "Oracle_Name_pi", "Task_Name", "Oracle_Name_ti", "Duration", "Comment_dh", "Comment_ti"]]
            export_day_df = export_day_df[export_day_df["Duration"].notna()]

            grouped_day_df = grouped_day_df[["Project_Name", "Project_Number", "Task_Name",
                                             "Task_Number", "Duration", "Billable", "Hourly_Rate", "Currency"]]

            return grouped_day_df, export_day_df
        except KeyError:
            grouped_day_df = pd.DataFrame(columns=["Project_Name", "Project_Number", "Task_Name",
                                             "Task_Number", "Duration", "Billable", "Hourly_Rate", "Currency"] )
            export_day_df = pd.DataFrame(columns=["Date", "Project_Name", "Oracle_Name_pi", "Task_Name", "Oracle_Name_ti", "Duration", "Comment_dh", "Comment_ti"] )

            return grouped_day_df, export_day_df


    def concatenate_daily_sum_db(self, date_days, year, week):
        """
        Called from : WeeklyHours_changed_week()

        :param date_days: The dates "yyyy-mm-dd" of  the selected week
        :param year: Used to name weekly SQL db
        :param week: Used to name weekly SQL db
        :return:
        """

        df_table = pd.DataFrame()  # empty dataframe to start iteration over Days
        df_export =pd.DataFrame()
        # Iterates over date (input) and attaches the day name
        # 1 - Sums the hours per project for that day
        # 2 - Renames Duration Column to the day name
        # 3 - Concat New Column (new day) to DF based on Project_ID, number and task
        for date, day in zip(date_days, self.weekly_hours_columns_days):

            merge_week_table, merge_week_export = Concatentate_tables.calculate_sum_up(self, date)
            df_merge_week_table = pd.DataFrame(merge_week_table)
            df_week_table = df_merge_week_table.rename(columns={"Duration": day})
            df_table = pd.concat([df_table, df_week_table], join='outer')

            df_merge_week_export = pd.DataFrame(merge_week_export)
            df_merge_week_export["Date"] = day
            df_export = pd.concat([df_export, df_merge_week_export], axis=0)
        df_export_duration = pd.pivot_table(df_export, index=["Project_Name", "Task_Name", "Oracle_Name_pi", "Oracle_Name_ti"], columns="Date", values="Duration").reset_index()
        df_export_comments = pd.pivot_table(df_export, index=["Project_Name", "Task_Name", "Oracle_Name_pi", "Oracle_Name_ti", "Comment_ti"], columns="Date", values="Comment_dh",aggfunc=lambda x: ' '.join(x)).reset_index()
        df_export_comments = df_export_comments.rename(columns={"Monday": "Monday_comment", "Tuesday": "Tuesday_comment", "Wednesday": "Wednesday_comment",
                                                                "Thursday": "Thursday_comment", "Friday": "Friday_comment", "Saturday": "Saturday_comment", "Sunday": "Sunday_comment"})
        df_final_export = df_export_duration.merge(df_export_comments, on = ["Project_Name", "Task_Name", "Oracle_Name_pi", "Oracle_Name_ti"])
        df_final_export["Time_Type"] = "Regular Hours"
        df_final_export["Arcadis_Country"] = self.country


        columns_list = ["Oracle_Name_pi", "Oracle_Name_ti", "Time_Type", "Arcadis_Country",
         "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Line_Total", "Comment_ti",
         "Monday_comment", "Tuesday_comment", "Wednesday_comment", "Thursday_comment","Friday_comment", "Saturday_comment", "Sunday_comment"]
        df_final_export = df_final_export.reindex(columns=columns_list)

       # Sums the hours worked per day per project
        df = df_table.groupby(["Project_Name", "Project_Number","Task_Name", "Task_Number", "Billable", "Hourly_Rate", "Currency"]).sum().reset_index()
        df["Project_ID"]= df["Project_Name"]+":\n   "+df["Task_Name"]

        # Reorder columns for safety
        weekly_hours_bil = df[
            ["Project_ID", "Project_Number", "Task_Number", "Billable", "Hourly_Rate", "Currency",
             "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]]

        # Fills data frame with float to use sum.
        fill_na = weekly_hours_bil[self.weekly_hours_columns_days].fillna(float(0.0))
        weekly_hours_bil["Total"] = round(fill_na[self.weekly_hours_columns_days].sum(axis=1), 2)
        # If no hours are worked for a project, that project is dropped from the dataframe
        weekly_hours_bil = weekly_hours_bil[weekly_hours_bil["Total"] != 0].reset_index(drop=True)
        if sum(weekly_hours_bil["Total"]) == 0:
            billability_percentage = "0"
            sum_revenue_cur = ["0"]
        else:
            sum_billable_hours = sum(weekly_hours_bil["Billable"].astype(float)*weekly_hours_bil["Total"])
            billability_percentage = str(round(sum_billable_hours / (sum(weekly_hours_bil["Total"]))*100,1))

            weekly_hours_bil["Revenue_Sum"] = (weekly_hours_bil["Billable"].astype(float)*weekly_hours_bil["Total"]*weekly_hours_bil["Hourly_Rate"].astype(float))
            sum_revenue = round(weekly_hours_bil.groupby(["Currency"]).Revenue_Sum.sum().reset_index(),2)

            sum_revenue_cur = sum_revenue["Revenue_Sum"].astype(str) + " " + sum_revenue["Currency"]

        if str(sum(weekly_hours_bil["Total"])) != "0":
            total_kpi_data = {"Year": str(year), "Week": str(week), "Total": str(sum(weekly_hours_bil["Total"])),
                          "Billable": billability_percentage, "Revenue": sum_revenue["Revenue_Sum"][0], "Currency": sum_revenue["Currency"][0]}
            total_kpi = pd.DataFrame([total_kpi_data])


            df_old_total_kpi = Get_db.get_total_kpi_db(self, self.local_database, self.total_kpi_columns)
            df_total_kpi = pd.concat([df_old_total_kpi, total_kpi]).drop_duplicates(['Year','Week'],keep='last').sort_values(['Year', 'Week'])
            df_total_kpi.reset_index(drop=True, inplace=True)
            # SQL commands
            db = SQL_Database(f"{self.local_database}")
            df_total_kpi.to_sql('total_kpi', db._conn, if_exists="replace", index=False)

            # Sums all hours worked and populates Total Label
        weekly_worked_hours = (str(round(weekly_hours_bil["Total"].sum(), 2)))

        # Defines name for weekly Database and pushes weekly hours DF to SQL

        total_db = weekly_hours_bil[["Project_ID", "Project_Number", "Task_Number", "Total"]].copy()
        total_db["Task_Number"] = total_db.Project_Number.str.cat(total_db.Task_Number, sep="-")
        weekly_hours = weekly_hours_bil[["Project_ID", "Project_Number", "Task_Number",
             "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Total"]].copy()
        # Sends weekly hours DF to DataFrameModel class to populate Weekly Hours tableview

        return df_final_export, weekly_hours, total_db, billability_percentage, sum_revenue_cur, weekly_worked_hours


