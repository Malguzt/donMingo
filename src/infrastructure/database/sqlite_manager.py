import sqlite3
import os

class SqliteManager:
    def __init__(self, db_path="bots.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    short_name TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL UNIQUE,
                    api_key TEXT NOT NULL,
                    bot_type TEXT NOT NULL DEFAULT 'guanaco'
                )
            """)
            conn.commit()

    def get_connection(self):
        return sqlite3.connect(self.db_path)
