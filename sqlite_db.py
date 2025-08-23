import sqlite3
from typing import List, Optional, Union


class SQLiteDB:
    def __init__(self, db_path: str = 'gitee.db'):
        """
        初始化数据库连接
        :param db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.in_transaction = False  # 事务状态标记

    def __enter__(self):
        """ 支持 with 上下文管理 """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ 退出上下文时自动提交/回滚 """
        if exc_type:  # 发生异常时回滚
            self.rollback()
        else:
            self.commit()
        self.close()

    def connect(self) -> None:
        """ 建立数据库连接 """
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # 返回字典格式结果
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            raise DatabaseConnectionError(f"数据库连接失败: {e}") from e

    def close(self) -> None:
        """ 关闭数据库连接 """
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def begin(self) -> None:
        """ 显式开启事务 """
        if not self.in_transaction:
            self.cursor.execute('BEGIN')
            self.in_transaction = True

    def commit(self) -> None:
        """ 提交事务 """
        if self.in_transaction:
            self.conn.commit()
            self.in_transaction = False

    def rollback(self) -> None:
        """ 回滚事务 """
        if self.in_transaction:
            self.conn.rollback()
            self.in_transaction = False

    def execute(
            self,
            sql: str,
            params: Union[tuple, dict, None] = None,
            auto_commit: bool = True
    ) -> int:
        """
        执行 SQL 语句
        :param sql: SQL 语句
        :param params: 参数元组或字典
        :param auto_commit: 是否自动提交
        :return: 影响的行数
        """
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)

            if auto_commit and not self.in_transaction:
                self.conn.commit()

            return self.cursor.rowcount
        except sqlite3.IntegrityError as e:
            raise DuplicateEntryError(f"唯一约束冲突: {e}") from e
        except sqlite3.Error as e:
            self.rollback()
            raise DatabaseError(f"SQL 执行失败: {e}") from e

    def executemany(
            self,
            sql: str,
            params_list: List[Union[tuple, dict]],
            auto_commit: bool = True
    ) -> int:
        """
        批量执行 SQL 语句
        :param sql: SQL 语句
        :param params_list: 参数列表
        :param auto_commit: 是否自动提交
        :return: 影响的总行数
        """
        try:
            self.cursor.executemany(sql, params_list)
            if auto_commit and not self.in_transaction:
                self.conn.commit()
            return self.cursor.rowcount
        except sqlite3.Error as e:
            self.rollback()
            raise DatabaseError(f"批量执行失败: {e}") from e

    def fetch_one(self, sql: str, params: Union[tuple, dict, None] = None) -> Optional[dict]:
        """
        获取单条记录
        :return: 字典或 None
        """
        self.execute(sql, params, auto_commit=False)
        result = self.cursor.fetchone()
        return dict(result) if result else None

    def fetch_all(self, sql: str, params: Union[tuple, dict, None] = None) -> List[dict]:
        """
        获取全部记录
        :return: 字典列表
        """
        self.execute(sql, params, auto_commit=False)
        return [dict(row) for row in self.cursor.fetchall()]

    def table_exists(self, table_name: str) -> bool:
        """ 检查表是否存在 """
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        return bool(self.fetch_one(sql, (table_name,)))

    def insert_or_ignore(self, table: str, data: dict) -> int:
        """
        插入或忽略重复记录
        :param table: 表名
        :param data: 数据字典
        :return: 插入的行数 (0 或 1)
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        sql = f"INSERT OR IGNORE INTO {table} ({columns}) VALUES ({placeholders})"
        return self.execute(sql, tuple(data.values()))
    
    def insert_or_update(self, table: str, data: dict, primary_key_column: str) -> int:
        """
        根据唯一列插入或更新单行数据
        （存在则更新其他字段，不存在则插入整行）

        :param table: 表名
        :param data: 数据字典（必须包含主键列）
        :param primary_key_column: 用于判断是否存在的唯一列名
        :return: 影响的行数（1=成功，0=失败）
        """
        if primary_key_column not in data:
            raise ValueError(f"数据中必须包含主键列 '{primary_key_column}'")

        # 分离主键和其他字段
        primary_key_value = data[primary_key_column]
        update_data = {k: v for k, v in data.items() if k != primary_key_column}

        # 生成 SET 子句
        set_clause = ", ".join([f"{col}=?" for col in update_data.keys()])

        # 构建完整 SQL
        sql = f"""
            INSERT INTO {table} ({', '.join(data.keys())})
            VALUES ({', '.join(['?'] * len(data))})
            ON CONFLICT({primary_key_column}) DO UPDATE SET {set_clause}
        """

        # 参数顺序：INSERT参数 + UPDATE参数（排除主键）
        params = list(data.values()) + list(update_data.values())

        try:
            return self.execute(sql, params)
        except sqlite3.IntegrityError as e:
            raise DuplicateEntryError(f"约束冲突: {e}") from e

    def batch_insert(self, table: str, data_list: List[dict]) -> int:
        """
        批量插入数据
        :return: 成功插入的行数
        """
        if not data_list:
            return 0

        columns = ', '.join(data_list[0].keys())
        placeholders = ', '.join(['?'] * len(data_list[0]))
        sql = f"INSERT OR IGNORE INTO {table} ({columns}) VALUES ({placeholders})"

        params = [tuple(item.values()) for item in data_list]
        return self.executemany(sql, params)


# 自定义异常类
class DatabaseError(Exception):
    """ 数据库操作基异常 """


class DatabaseConnectionError(DatabaseError):
    """ 连接相关异常 """


class DuplicateEntryError(DatabaseError):
    """ 唯一约束冲突异常 """