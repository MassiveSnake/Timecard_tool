# loading in modules
import sqlite3

# creating file path
dbfile = 'C:\\Users\\stamb3257\\PYTHON_Projects\\Uren_Excel_automatisering\\Hour_Database.db'
# Create a SQL connection to our SQLite database
con = sqlite3.connect(dbfile)

# creating cursor
cur = con.cursor()



# reading all table names
table_list = [a for a in cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
# here is you table list
print(table_list)
# for row in cur.execute("SELECT * FROM 'Year_2023_Week_2';"):
#     print(row)

# Be sure to close the connection
con.close()