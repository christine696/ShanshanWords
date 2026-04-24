import csv
import os
import sqlite3

DB_NAME = "words.db"
CSV_PATH = os.path.join("data", "words_master.csv")


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS words")
    cursor.execute("DROP TABLE IF EXISTS progress")

    cursor.execute("""
    CREATE TABLE words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL,
        category TEXT NOT NULL,
        section TEXT,
        subcategory TEXT,
        phonetic TEXT,
        part_of_speech TEXT,
        meaning_cn TEXT,
        example_en TEXT,
        example_cn TEXT,
        source TEXT,
        difficulty INTEGER DEFAULT 1
    )
    """)

    cursor.execute("""
    CREATE TABLE progress (
        word_id INTEGER PRIMARY KEY,
        is_favorite INTEGER DEFAULT 0,
        is_hard INTEGER DEFAULT 0,
        FOREIGN KEY (word_id) REFERENCES words(id)
    )
    """)

    if not os.path.exists(CSV_PATH):
        print(f"找不到 CSV 文件: {CSV_PATH}")
        conn.commit()
        conn.close()
        return

    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = (row.get("word") or "").strip()
            category = (row.get("category") or "").strip()

            if not word or not category:
                continue

            difficulty_raw = row.get("difficulty")
            try:
                difficulty = int(difficulty_raw) if difficulty_raw not in (None, "") else 1
            except ValueError:
                difficulty = 1

            cursor.execute("""
                INSERT INTO words
                (word, category, section, subcategory, phonetic, part_of_speech, meaning_cn, example_en, example_cn, source, difficulty)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                word,
                category,
                row.get("section", ""),
                row.get("subcategory", ""),
                row.get("phonetic", ""),
                row.get("part_of_speech", ""),
                row.get("meaning_cn", ""),
                row.get("example_en", ""),
                row.get("example_cn", ""),
                row.get("source", ""),
                difficulty
            ))

            word_id = cursor.lastrowid
            cursor.execute("""
                INSERT INTO progress (word_id, is_favorite, is_hard)
                VALUES (?, 0, 0)
            """, (word_id,))

    conn.commit()
    conn.close()
    print("数据库初始化完成，words.db 已生成。")


if __name__ == "__main__":
    init_db()
