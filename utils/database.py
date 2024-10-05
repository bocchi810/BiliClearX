import sqlite3
from pathlib import Path


class SQlite:
    def __init__(
        self,
        db_name: str = str(
            Path(__file__).resolve().parent.parent / "configs" / "biliclear.db"
        ),
    ):
        self.db_name = db_name
        self.connection = None
        self.create_table_if_not_exists(
        'report',
        {
            'id': 'INTEGER PRIMARY KEY',
            'rpid': 'TEXT',
            'oid': 'TEXT',
            'mid': 'TEXT',
            'content': 'TEXT NOT NULL',
            'rule': 'TEXT',
            'is_reported': 'INTEGER DEFAULT 0',
            'need_report': 'INTEGER DEFAULT 0',
            'report_time': 'TIMESTAMP',
            'time': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
        }
    )

    def _get_connection(self):
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_name)
        return self.connection
    
    def _get_columns(self, table):
        """
        获取表的所有列名。
        :param table: 表名
        :return: 列名列表
        """
        cursor = self.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        return columns

    def execute(self, sql, params=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            conn.commit()
            return cursor
        except Exception as e:
            conn.rollback()
            raise e

    def create_table_if_not_exists(self, table_name: str, fields: dict):
        """
        检查指定的表是否已存在，如果不存在则创建它。
        :param table_name: 表名
        :param fields: 字段定义，键为字段名，值为SQL字段类型字符串
        """
        create_table_sql = (
            f"CREATE TABLE IF NOT EXISTS {table_name} ("
            + ", ".join([f"{name} {type}" for name, type in fields.items()])
            + ")"
        )
        self.execute(create_table_sql)

    def insert(self, table, data):
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        self.execute(sql, list(data.values()))

    def delete(self, table, condition):
        sql = f"DELETE FROM {table} WHERE {condition}"
        self.execute(sql)

    def select_all(self, table):
        columns = self._get_columns(table)
        sql = f"SELECT * FROM {table}"
        cursor = self.execute(sql)
        results = cursor.fetchall()
        return [dict(zip(columns, row)) for row in results]

    def select_where(self, table, condition):
        columns = self._get_columns(table)
        sql = f"SELECT * FROM {table} WHERE {condition}"
        cursor = self.execute(sql)
        results = cursor.fetchall()
        return [dict(zip(columns, row)) for row in results]

    def update(self, table, data, condition):
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {condition}"
        self.execute(sql, list(data.values()))

    def close(self):
        if self.connection:
            self.connection.close()

Database = SQlite()