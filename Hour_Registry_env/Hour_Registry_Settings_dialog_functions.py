from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal, QSettings
from QT_Files.Hour_Registry_Settings_QT import Ui_Settings_dialog


class Settings_dialog(QDialog, Ui_Settings_dialog):
    window_closed = pyqtSignal()

    def __init__(self, parent=None):
        super(Settings_dialog, self).__init__(parent)
        self.setupUi(self)
        self.populate_settings()

    def closeEvent(self, event):
        self.window_closed.emit()
        event.accept()

    def populate_settings(self):
        country, company, local_db, currency, roundup, resolution = self.set_settings()
        if roundup == "true":
            roundup_bool = True
        else:
            roundup_bool = False
        self.lineEdit_country.setText(country)
        self.lineEdit_company.setText(company)
        self.lineEdit_local_db.setText(local_db)
        self.comboBox_currency.setCurrentText(currency)
        self.checkBox_round.setChecked(roundup_bool)
        self.comboBox_round_resolution.setCurrentIndex(int(resolution))

    def edit_settings(self):
        country = self.lineEdit_country.text()
        company = self.lineEdit_company.text()
        local_db = self.lineEdit_local_db.text()
        if local_db[-3:] != ".db":
            type = "Invalid Database extension"
            text = "Please edit the extension"
            info = "Make sure the database name ends with .db"
            self.messagebox(type, text, info)
            return None
        currency = self.comboBox_currency.currentText()
        roundup = self.checkBox_round.isChecked()
        resolution = self.comboBox_round_resolution.currentIndex()

        check_none_list = [country, company, local_db, currency, roundup, resolution]
        if any(elem == "" for elem in check_none_list) == True:
            type = "Empty setting values"
            text = "Some field(s) are not defined"
            info = "Please make sure that every setting has an value"
            self.messagebox(type, text, info)
            return None

        self.set_country.setValue("country", country)
        self.set_company.setValue("company", company)
        self.set_local_database.setValue("local_database", local_db)
        self.set_currency.setValue("currency", currency)
        self.set_roundup.setValue("roundup", roundup)
        self.set_resolution.setValue("resolution", resolution)

        self.close()

    def set_settings(self):

        self.set_local_database = QSettings("MyMainWindow", "local_database")
        self.set_country = QSettings("MyMainWindow", "country")
        self.set_company = QSettings("MyMainWindow", "company")
        self.set_currency = QSettings("MyMainWindow", "currency")
        self.set_roundup = QSettings("MyMainWindow", "roundup")
        self.set_resolution = QSettings("MyMainWindow", "resolution")

        settings = [self.set_country, self.set_company, self.set_currency, self.set_local_database, self.set_roundup, self.set_resolution]
        setting_parameter = ["country", "company", "currency", "local_database", "roundup", "resolution"]
        init_setting = ["Germany", "Arcadis", "€ Euro", "Hour_Database.db", "false", "2"]

        for item, para, init in zip(settings, setting_parameter, init_setting):
            if item.value(para) == None:
                item.setValue(para, init)

        return self.set_country.value("country"), self.set_company.value("company"), self.set_local_database.value(
            "local_database"), \
               self.set_currency.value("currency"), self.set_roundup.value("roundup"), self.set_resolution.value(
            "resolution")

    def messagebox(self, type, text, info):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Error: " + type)
        msg.setText(text)
        msg.setInformativeText(info)
        msg.exec()
        return None