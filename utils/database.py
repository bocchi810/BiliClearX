import aiosqlite
from utils.config import ROOT


class Database:
    def __init__(self, db_name: str = str(ROOT / "configs" / "biliclear.db")):
        self.db_name = db_name

    async def _get_connection(self):
        return await aiosqlite.connect(self.db_name)

    # 异步执行SQL语句
    async def execute(self, sql, params=None):
        async with await self._get_connection() as conn:
            async with conn.cursor() as cursor:
                if params:
                    await cursor.execute(sql, params)
                else:
                    await cursor.execute(sql)
                await conn.commit()
                return cursor

    # 插入数据
    async def insert(self, table, data):
        columns = ', '.join(data.keys())
        placeholders = ', '.join('?' * len(data))
        sql = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'
        await self.execute(sql, list(data.values()))

    # 删除数据
    async def delete(self, table, condition):
        sql = f'DELETE FROM {table} WHERE {condition}'
        await self.execute(sql)

    # 查询所有数据
    async def select_all(self, table):
        sql = f'SELECT * FROM {table}'
        async with await self._get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql)
                return await cursor.fetchall()

    # 条件查询
    async def select_where(self, table, condition):
        sql = f'SELECT * FROM {table} WHERE {condition}'
        async with await self._get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql)
                return await cursor.fetchall()

    # 更新数据
    async def update(self, table, data, condition):
        set_clause = ', '.join([f'{k} = ?' for k in data.keys()])
        sql = f'UPDATE {table} SET {set_clause} WHERE {condition}'
        await self.execute(sql, list(data.values()))
