import os
import sqlite3
from typing import Dict, Tuple, List, Any

class DataBase():
    def __init__(self, file):
        self.file = file
        self.file_name = self.file.split('.')[0]
        self.path = os.path.dirname(os.path.realpath(__file__))
        self._conn = sqlite3.connect(self.path + '/' + self.file)
        self._cur = self._conn.cursor()
        
    def create_table(self, table) -> None:
        self._cur.execute(table)
        print('Command executed succesfull...')
        self._conn.commit()
    
    def insert_data(self, data: List[Tuple]) -> None:
        marks = ['?' for _ in data[0]]
        marks = f'({",".join(marks)})'
        self._cur.executemany(f"INSERT INTO {self.file_name} VALUES {marks} ", data)
        print('Command executed succesfull...')
        self._conn.commit()
    

    def fetch_all(self) -> List[Tuple]:
        self._cur.execute("SELECT * FROM {}".format(self.file_name))
        return self._cur.fetchall()

    def select_data(self, placeholder: str, query: Any) -> List[Tuple]:
        self._cur.execute("SELECT * FROM {} WHERE {} == '{}' ".format(
            self.file_name, placeholder, query))
        return self._cur.fetchall()

    def close(self):
        self._conn.close()


if __name__ == '__main__':
    db = DataBase('users.db')

    table = """CREATE TABLE users(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT,
                            url_image TEXT,
                            subaccount TEXT,
                            symbol TEXT,
                            api_key TEXT,
                            api_secret TEXT,
                            post_only REAL,
                            capital REAL,
                            leverage REAL,
                            up_zone REAL,
                            down_zone REAL,
                            minimum_delta_position REAL,
                            minimum_percent_change REAL,
                            allow_live_trading REAL
                            )"""

    #db.create_table(table)
    #users = [(None,3,4,5,6,7,8,9,10,11,12,13,14,15,16)]
    #db.insert_data(users)