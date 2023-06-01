# loading in modules
import sqlite3
from PyQt5.QtCore import pyqtSignal, QSettings

# creating file path
#dbfile = 'C:\\Users\\stamb3257\\PYTHON_Projects\\arc-hours-registry-project\\Hour_Registry_env\\Hour_Database.db'
dbfile = 'C:\\Users\\stamb3257\\AppData\\Local\\Programs\\Hour Registry Tool\\Hour_Database.db'
# Create a SQL connection to our SQLite database
con = sqlite3.connect(dbfile)

# creating cursor
cur = con.cursor()
#
#cur.execute("DROP TABLE IF EXISTS 'total';")
#
# cur.execute("DELETE FROM projects WHERE id_pi ='6'")

# cur.execute("ALTER TABLE Quenctic RENAME TO Quentic;")
# cur.execute("Update 'projects' set Project_Name = 'Quentic' WHERE Project_Name = 'Quenctic'")
# cur.execute("Update 'Business_Advisory' set Task_Name = 'Strategy' WHERE Task_Name = 'Awaiting_Project_code'")
# con.commit()

setting = QSettings("MyMainWindow", "local_database")
setting.clear()
setting = QSettings("MyMainWindow", "country")
setting.clear()
setting = QSettings("MyMainWindow", "company")
setting.clear()
setting = QSettings("MyMainWindow", "currency")
setting.clear()
setting = QSettings("MyMainWindow", "roundup")
setting.clear()
setting = QSettings("MyMainWindow", "resolution")
setting.clear()

#reading all table names
table_list = [a for a in cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
# here is you table list
print(table_list)
for row in cur.execute("SELECT * FROM 'projects';"):
     print(row)

names = list(map(lambda x: x[0], cur.description))
print(names)
# Be sure to close the connection
con.close()