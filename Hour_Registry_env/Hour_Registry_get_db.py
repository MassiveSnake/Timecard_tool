from Hour_Registry_SQL import SQL_Database
from Hour_Registry_Settings_dialog_functions import Settings_dialog
import pandas as pd
import sqlite3

class Get_db:


    def get_project_db(self, database, columns):
        """
        Opens SQL projects Table
        and converts it into Panda Dataframe
        :return: Project Panda DF
        """

        # Creating/ Opening Project Table, based on LineEdit inputs
        sql = ("CREATE TABLE IF NOT EXISTS projects "
               "(id_pi integer PRIMARY KEY, "
               "Client text, "
               "Project_Name text, "
               "Project_Number text, "
               "Oracle_Name_pi text, "
               "Project_Manager text, "
               "Client_Contact text, "
               "Additional_information_pi text )")
        db = SQL_Database(f"{database}") # Calls the Database name described in INIT
        db.execute(sql)

        # Opens Project SQL database as Panda DataFrame
        sql_query = pd.read_sql_query("SELECT * FROM projects", db._conn)
        df = pd.DataFrame(sql_query, columns = columns)
        db.close()
        return df

    def get_project_edit_db(self, database, project_name, columns):

        db = SQL_Database(f"{database}") # Calls the Database name described in INIT

        # Opens Project SQL database as Panda DataFrame
        sql = f"""SELECT * FROM projects WHERE Project_Name = '{project_name}'"""
        sql_query = pd.read_sql_query(sql , db._conn)
        df = pd.DataFrame(sql_query, columns = columns)
        db.close()
        return df

    def get_task_db(self, database, project, columns):
        """
        Opens SQL project selected Table

        :return: task list
        """

        if project == "":
            pass
        else:
            sql =   ("CREATE TABLE IF NOT EXISTS '{table}' " \
                "(id_ti integer PRIMARY KEY, " \
                "Task_Name text, " \
                "Task_Number text, "\
                "Oracle_Name_ti text, "\
                "Billable text, "\
                "Hourly_Rate text, "\
                "Currency text, "\
                "Comment_ti text )".format(table=project))
            db = SQL_Database(f"{database}") # Calls the Database name described in INIT
            db.execute(sql)

        # Opens Project SQL database as Panda DataFrame
            sql = ("SELECT * FROM {tab}".format(tab=project))

            sql_query = pd.read_sql_query(sql, db._conn)
            df = pd.DataFrame(sql_query, columns=columns)
            db.close()
            return df

    def get_task_edit_db(self, database, project_name, task_name, columns):

        db = SQL_Database(f"{database}") # Calls the Database name described in INIT

        # Opens Project SQL database as Panda DataFrame
        sql = f"""SELECT * FROM '{project_name}' WHERE Task_Name = '{task_name}'"""
        sql_query = pd.read_sql_query(sql , db._conn)
        df = pd.DataFrame(sql_query, columns = columns)
        db.close()
        return df




    def get_daily_db(self, database, columns):
        """
         Opens SQL daily Table
         and converts it into Panda Dataframe
         :return: Daily Hours Panda DF
         """
        # Creating/ Opening Daily worked hours Table, based on LineEdit inputs
        sql = ("CREATE TABLE IF NOT EXISTS daily "
               "(id_dh integer PRIMARY KEY,"
               "Date text, "
               "Start text, "
               "End text, "
               "Duration text, "
               "Project_Name text, "
               "Oracle_Name_pi text, "
               "Task_Name text, "
               "Oracle_Name_ti text, "
               "Comment_dh text )")
        db = SQL_Database(f"{database}")
        db.execute(sql)

        # Opens Daily Hours SQL database as Panda DataFrame
        sql_query = pd.read_sql_query("SELECT * FROM daily", db._conn)
        df = pd.DataFrame(sql_query, columns = columns)
        db.close()
        return df

    def get_daily_edit_db(self, database, date, start, end,  columns):
        db = SQL_Database(f"{database}") # Calls the Database name described in INIT

        # Opens Project SQL database as Panda DataFrame
        sql = f"""SELECT * FROM daily WHERE Date = '{date}' AND Start = '{start}' AND End = '{end}' """

        sql_query = pd.read_sql_query(sql , db._conn)
        df = pd.DataFrame(sql_query, columns = columns)
        db.close()

        return df

    def get_daily_day_db(self, database, date, columns):
        """
         Opens SQL daily Table
         and converts it into Panda Dataframe
         :return: Daily Hours Panda DF
         """
        # Creating/ Opening Daily worked hours Table, based on LineEdit inputs
        sql = ("CREATE TABLE IF NOT EXISTS daily "
               "(id_dh integer PRIMARY KEY,"
               "Date text, "
               "Start text, "
               "End text, "
               "Duration text, "
               "Project_Name text, "
               "Oracle_Name_pi text, "
               "Task_Name text, "
               "Oracle_Name_ti text, "
               "Comment_dh text )")
        db = SQL_Database(f"{database}")
        db.execute(sql)

        # Opens Daily Hours SQL database as Panda DataFrame
        sql_query = pd.read_sql_query(f"SELECT * FROM daily Where Date = '{date}' ", db._conn)
        df = pd.DataFrame(sql_query, columns = columns)
        db.close()
        return df

    def get_total_db(self, database):
        """
        Opens SQL total Table
        and converts it into Panda Dataframe
        :return: Total Panda DF
        """
        db = SQL_Database(f"{database}")
        # Opens Daily Hours SQL database as Panda DataFrame
        sql_query = pd.read_sql_query("SELECT * FROM total", db._conn)
        df = pd.DataFrame(sql_query)
        db.close()
        return df

    def get_total_kpi_db(self, database, columns):
        """
        Opens SQL total Table
        and converts it into Panda Dataframe
        :return: Total Panda DF
        """
        sql = ("CREATE TABLE IF NOT EXISTS total_kpi "
               "(id_total_kpi integer PRIMARY KEY, "
               "Year text, "
               "Week text, "
               "Total text, "
               "Billable text, "
               "Revenue text ,"
               "Currency text )")
        db = SQL_Database(f"{database}") # Calls the Database name described in INIT
        db.execute(sql)

        sql_query = pd.read_sql_query("SELECT * FROM total_kpi", db._conn)
        df = pd.DataFrame(sql_query, columns = columns)
        db.close()
        return df

