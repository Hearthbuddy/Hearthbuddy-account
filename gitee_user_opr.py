import os
import sqlite3

def create_table():
    conn = sqlite3.connect('gitee.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS USERS (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                USERID TEXT UNIQUE,
                HARDWAREID TEXT
            )
        ''')
        conn.commit()
        print("表创建成功！")
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
    finally:
        conn.close()


def import_ids_to_db():
    # 连接数据库
    conn = sqlite3.connect('gitee.db')
    cursor = conn.cursor()

    # 遍历ids目录
    ids_dir = 'ids'
    inserted_count = 0
    skipped_count = 0

    try:
        # 使用scandir更高效地遍历目录
        with os.scandir(ids_dir) as entries:
            for entry in entries:
                if entry.is_file():
                    giteeuserid = entry.name
                    filepath = entry.path

                    try:
                        # 读取文件内容
                        with open(filepath, 'r') as f:
                            hardwareid = f.read().strip()  # 去除首尾空白

                            # 插入数据库（使用参数化查询防止SQL注入）
                            cursor.execute('''
                                           INSERT
                                           OR IGNORE INTO USERS 
                                (USERID, HARDWAREID)
                                VALUES (?, ?)
                                           ''', (giteeuserid, hardwareid))

                            # 统计插入结果
                            if cursor.rowcount > 0:
                                inserted_count += 1
                            else:
                                skipped_count += 1

                    except IOError as e:
                        print(f"无法读取文件 {filepath}: {e}")

        # 提交所有更改
        conn.commit()
        print(f"操作完成！成功插入 {inserted_count} 条，跳过 {skipped_count} 条重复记录")

    except FileNotFoundError:
        print(f"目录 {ids_dir} 不存在")
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
    finally:
        conn.close()


if __name__ == '__main__':
    create_table()
    import_ids_to_db()