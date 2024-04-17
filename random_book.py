import sqlite3
import random

def pick_random_book(db_path):
    # 连接到 SQLite 数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 查询数据库中所有书籍的 ID
    cursor.execute("SELECT id FROM books")
    book_ids = cursor.fetchall()  # 获取所有的书籍 ID

    # 如果没有书籍，返回 None
    if not book_ids:
        print("No books found in the database.")
        return None

    # 随机选择一个书籍 ID
    random_id = random.choice(book_ids)[0]

    # 根据 ID 获取书籍的详细信息
    cursor.execute("SELECT title, author_sort FROM books WHERE id=?", (random_id,))
    book_info = cursor.fetchone()  # 获取书籍信息

    # 关闭数据库连接
    conn.close()

    # 返回书籍信息
    return book_info

# 使用示例
db_path = 'path_to_your_calibre_metadata.db'  # Calibre 数据库文件的路径
book = pick_random_book(db_path)
if book:
    print(f"Randomly selected book: {book[0]} by {book[1]}")
else:
    print("Failed to retrieve a book.")
    