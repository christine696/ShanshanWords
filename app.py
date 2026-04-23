import math
import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
DB_NAME = "words.db"


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/library")
def library():
    return render_template("library.html")


@app.route("/words")
def words():
    category = request.args.get("category", "IELTS")
    q = request.args.get("q", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    if q:
        cursor.execute("""
            SELECT w.*, p.is_favorite, p.is_hard
            FROM words w
            LEFT JOIN progress p ON w.id = p.word_id
            WHERE w.category = ?
              AND (w.word LIKE ? OR w.meaning_cn LIKE ?)
            ORDER BY w.word ASC
        """, (category, f"%{q}%", f"%{q}%"))
    else:
        cursor.execute("""
            SELECT w.*, p.is_favorite, p.is_hard
            FROM words w
            LEFT JOIN progress p ON w.id = p.word_id
            WHERE w.category = ?
            ORDER BY w.word ASC
        """, (category,))

    words_list = cursor.fetchall()
    conn.close()

    return render_template("words.html", words=words_list, category=category, q=q)


@app.route("/toggle_favorite/<int:word_id>")
def toggle_favorite(word_id):
    next_url = request.args.get("next") or url_for("words")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT is_favorite FROM progress WHERE word_id = ?", (word_id,))
    row = cursor.fetchone()

    if row:
        new_value = 0 if row["is_favorite"] == 1 else 1
        cursor.execute(
            "UPDATE progress SET is_favorite = ? WHERE word_id = ?",
            (new_value, word_id)
        )

    conn.commit()
    conn.close()
    return redirect(next_url)


@app.route("/toggle_hard/<int:word_id>")
def toggle_hard(word_id):
    next_url = request.args.get("next") or url_for("words")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT is_hard FROM progress WHERE word_id = ?", (word_id,))
    row = cursor.fetchone()

    if row:
        new_value = 0 if row["is_hard"] == 1 else 1
        cursor.execute(
            "UPDATE progress SET is_hard = ? WHERE word_id = ?",
            (new_value, word_id)
        )

    conn.commit()
    conn.close()
    return redirect(next_url)


@app.route("/favorites")
def favorites():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT w.*, p.is_favorite, p.is_hard
        FROM words w
        JOIN progress p ON w.id = p.word_id
        WHERE p.is_favorite = 1
        ORDER BY w.category, w.word ASC
    """)

    favorite_words = cursor.fetchall()
    conn.close()

    return render_template("favorites.html", words=favorite_words)


@app.route("/hard_words")
def hard_words():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT w.*, p.is_favorite, p.is_hard
        FROM words w
        JOIN progress p ON w.id = p.word_id
        WHERE p.is_hard = 1
        ORDER BY w.category, w.word ASC
    """)

    hard_words_list = cursor.fetchall()
    conn.close()

    return render_template("hard_words.html", words=hard_words_list)


@app.route("/method", methods=["GET", "POST"])
def method():
    if request.method == "POST":
        category = request.form.get("category", "IELTS")
        cycle_days = int(request.form.get("cycle_days", 4))
        day_number = int(request.form.get("day_number", 1))
        return redirect(url_for(
            "plan",
            category=category,
            cycle_days=cycle_days,
            day_number=day_number
        ))

    return render_template("method.html")


@app.route("/plan")
def plan():
    category = request.args.get("category", "IELTS")
    cycle_days = int(request.args.get("cycle_days", 4))
    day_number = int(request.args.get("day_number", 1))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT w.*, p.is_favorite, p.is_hard
        FROM words w
        LEFT JOIN progress p ON w.id = p.word_id
        WHERE w.category = ?
        ORDER BY w.id ASC
    """, (category,))
    all_words = cursor.fetchall()

    total_words = len(all_words)

    if total_words == 0:
        conn.close()
        return render_template(
            "plan.html",
            words=[],
            hard_words=[],
            category=category,
            cycle_days=cycle_days,
            day_number=day_number,
            total_words=0,
            per_day=0,
            start_index=0,
            end_index=0
        )

    per_day = math.ceil(total_words / cycle_days)

    start_index = (day_number - 1) * per_day
    end_index = min(start_index + per_day, total_words)

    today_words = all_words[start_index:end_index]

    cursor.execute("""
        SELECT w.*, p.is_favorite, p.is_hard
        FROM words w
        JOIN progress p ON w.id = p.word_id
        WHERE p.is_hard = 1 AND w.category = ?
        ORDER BY w.word ASC
    """, (category,))
    hard_words_list = cursor.fetchall()

    conn.close()

    return render_template(
        "plan.html",
        words=today_words,
        hard_words=hard_words_list,
        category=category,
        cycle_days=cycle_days,
        day_number=day_number,
        total_words=total_words,
        per_day=per_day,
        start_index=start_index + 1,
        end_index=end_index
    )


if __name__ == "__main__":
    app.run(debug=True)