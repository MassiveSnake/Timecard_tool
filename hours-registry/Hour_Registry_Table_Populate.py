from PyQt5 import QtCore
from PyQt5.QtWidgets import QHeaderView
from Hour_Registry_SQL import SQL_Database


import pandas as pd

class DataFrameModel(QtCore.QAbstractTableModel):
    DtypeRole = QtCore.Qt.UserRole + 1000
    ValueRole = QtCore.Qt.UserRole + 1001

    def __init__(self, df=pd.DataFrame(), parent=None):
        super(DataFrameModel, self).__init__(parent)
        self._dataframe = df
        self.hour_database = "Hour_Database.db"
        if df.columns[1] == "Client":
            self.database = "projects"
            self.id_key = "id_pi"
        elif df.columns[1] == "Start":
            self.database = "daily"
            self.id_key = "id_dh"
        elif df.columns[1] == "Duration":
            self.database = "daily_sum"
            self.id_key = "id_sum_dh"




    def setDataFrame(self, dataframe):
        self.beginResetModel()
        self._dataframe = dataframe.copy()
        self._dataframe.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.endResetModel()

    def dataFrame(self):
        return self._dataframe

    dataFrame = QtCore.pyqtProperty(pd.DataFrame, fget=dataFrame, fset=setDataFrame)


    @QtCore.pyqtSlot(int, QtCore.Qt.Orientation, result=str)
    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self._dataframe.columns[section]
            else:
                return str(self._dataframe.index[section])
        return QtCore.QVariant()

    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._dataframe.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid():
            return 0
        return self._dataframe.columns.size

    def setData(self, index, value, role):

        if role == QtCore.Qt.EditRole:

            self._dataframe.iloc[index.row(),index.column()] = value
            column = self._dataframe.columns[index.column()]
            row = index.row()+1

            db = SQL_Database(f"{self.hour_database}")
            sql = "UPDATE '" + self.database + "' SET '" + column + "' = '" + value + "' WHERE "+ self.id_key +" = '" + str(row) + "' "

            db.execute(sql)
            db.close()

            return True
        return False


    def data(self, index, role=None):

        if not index.isValid() or not (0 <= index.row() < self.rowCount() \
                                       and 0 <= index.column() < self.columnCount()):
            return QtCore.QVariant()
        row = self._dataframe.index[index.row()]
        col = self._dataframe.columns[index.column()]
        dt = self._dataframe[col].dtype

        val = self._dataframe.iloc[row][col]

        if role == QtCore.Qt.DisplayRole or role==QtCore.Qt.EditRole:
            return str(val)

        elif role == DataFrameModel.ValueRole:
            return val
        if role == DataFrameModel.DtypeRole:
            return dt
        return QtCore.QVariant()

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled

        return super().flags(index) | QtCore.Qt.ItemIsEditable


    def roleNames(self):
        roles = {
            QtCore.Qt.DisplayRole: b'display',
            DataFrameModel.DtypeRole: b'dtype',
            DataFrameModel.ValueRole: b'value'
        }
        return roles

