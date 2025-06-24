import sqlite3
import pandas as pd
from PyQt5 import QtWidgets

class ArtisanToolBox:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def fetch_data(self, query):
        try:
            df = pd.read_sql_query(query, self.conn)
            return df
        except Exception as e:
            QtWidgets.QMessageBox.critical(None, "Database Error", str(e))
            return None

    def close_connection(self):
        self.conn.close()