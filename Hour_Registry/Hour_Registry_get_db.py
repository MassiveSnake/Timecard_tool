from Hour_Registry_SQL import SQL_Database
import pandas as pd

class Get_db:
    def __init__(self):
        self.hour_database = "Hour_Database.db"

    def get_project_db(self, columns):
        """
        Opens SQL projects Table
        and converts it into Panda Dataframe
        :return: Project Panda DF
        """
        # Creating/ Opening Project Table, based on LineEdit inputs
        sql = ("CREATE TABLE IF NOT EXISTS projects "
               "(id_pi integer PRIMARY KEY, "
               "Project_ID text, "
               "Client text, "
               "Project_Name text, "
               "Project_Number number, "
               "Task_Number text, "
               "Hourly_Rate number, "
               "Currency text, "
               "Project_Manager text, "
               "Client_Contact text, "
               "Additional_information_pi text )")
        db = SQL_Database(self.hour_database) # Calls the Database name described in INIT
        db.execute(sql)

        # Opens Project SQL database as Panda DataFrame
        sql_query = pd.read_sql_query("SELECT * FROM projects", db._conn)
        df = pd.DataFrame(sql_query, columns = columns)
        db.close()
        return df

    def get_project_edit_db(self, project_id, columns):

        db = SQL_Database(f"{self.hour_database}") # Calls the Database name described in INIT

        # Opens Project SQL database as Panda DataFrame
        sql = f"""SELECT * FROM projects WHERE id_pi = {project_id}"""
        sql_query = pd.read_sql_query(sql , db._conn)
        df = pd.DataFrame(sql_query, columns = columns)
        db.close()
        return df

    def get_daily_edit_db(self, date, start, end,  columns):

        db = SQL_Database(f"{self.hour_database}") # Calls the Database name described in INIT

        # Opens Project SQL database as Panda DataFrame
        sql = f"""SELECT * FROM daily WHERE Date = '{date}' AND Start = '{start}' AND End = '{end}' """

        sql_query = pd.read_sql_query(sql , db._conn)
        df = pd.DataFrame(sql_query, columns = columns)
        db.close()

        return df


    def get_daily_db(self, columns):
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
               "Project_ID text, "
               "Additional_information_dh text )")
        db = SQL_Database(self.hour_database)
        db.execute(sql)

        # Opens Daily Hours SQL database as Panda DataFrame
        sql_query = pd.read_sql_query("SELECT * FROM daily", db._conn)
        df = pd.DataFrame(sql_query, columns = columns)
        db.close()
        return df

    # def get_daily_sum_db(self, date, columns):
    #     """
    #     Creates SQL daily database with cummulative hours per project
    #     :param date: Input date which needs to be summed
    #     :return: Daily cummulative hours per project Panda Dataframe
    #     """
    #     # Creating / Replacing Daily Hours SUM table
    #     parameter = (date,)
    #     sql = ("CREATE TABLE IF NOT EXISTS ?  "
    #            "(id_sum_dh integer PRIMARY KEY,"
    #             "Project_ID text, "
    #             "Project_Number, "
    #             "Task_Number, "
    #             "Duration text)")
    #     db = SQL_Database(self.hour_database)
    #     db.execute(sql, parameter) # SQL command: parameter is a variable which is inserted on the ? place.
    #
    #     # Opens Daily Hours SQL database as Panda DataFrame
    #     sql_query = pd.read_sql_query(("SELECT * FROM ? ", date), db._conn)
    #     df = pd.DataFrame(sql_query, columns=columns)
    #     db.close()
    #     return df