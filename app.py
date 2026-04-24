import math, os, sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
DB_NAME = "words.db"

CATEGORIES = {
    "GRE": {
        "label": "GRE核心词汇",
        "desc": "GRE 考试高频词汇，攻克学术英语",
        "icon": "🎓",
    },
    "IELTS_BOOK": {
        "label": "雅思词汇真经",
        "desc": "雅思真经 22 章节，系统深度掌握",
        "icon": "📖",
    },
    "IELTS_SCENE": {
        "label": "雅思场景词汇",
        "desc": "听说读写四大篇章，精准场景覆盖",
        "icon": "🎧",
    },
}

SCENE_SECTIONS = ["听力词汇篇", "阅读词汇篇", "写作词汇篇", "口语词汇篇"]


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def get_counts():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT category, COUNT(*) as cnt FROM words GROUP BY category")
    result = {r["category"]: r["cnt"] for r in cur.fetchall()}
    conn.close()
    return result


def get_bible_chapters():
    """从数据库动态读取IELTS_BOOK的章节列表（按章节号排序）"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT section FROM words
        WHERE category='IELTS_BOOK' AND section IS NOT NULL AND section!=''
        ORDER BY section
    """)
    chapters = [r["section"] for r in cur.fetchall()]
    conn.close()
    return chapters


@app.route("/")
def index():
    print("[ACTIVE] index() called - rendering index.html")
    cat_counts = get_counts()
    print(f"[ACTIVE] cat_counts = {cat_counts}")
    total = sum(cat_counts.values())
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM words WHERE id IN (SELECT word_id FROM progress WHERE is_favorite=1)")
    fav = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM words WHERE id IN (SELECT word_id FROM progress WHERE is_hard=1)")
    hard = cur.fetchone()[0]
    conn.close()
    return render_template("index.html", cat_counts=cat_counts, total=total,
                           fav=fav, hard=hard, cats=CATEGORIES)


@app.route("/library")
def library():
    print("[ACTIVE] library() called - rendering library.html")
    cat_counts = get_counts()
    return render_template("library.html", cat_counts=cat_counts, cats=CATEGORIES)


@app.route("/library/<cat>")
def library_cat(cat):
    if cat not in CATEGORIES:
        return redirect(url_for("library"))

    cat_counts = get_counts()
    count = cat_counts.get(cat, 0)
    label = CATEGORIES[cat]["label"]

    print(f"[ACTIVE] /library/{cat} -> {CATEGORIES[cat]['label']}")

    if cat == "GRE":
        print(f"[ACTIVE] Rendering library_gre.html for GRE")
        return render_template("library_gre.html", cats=CATEGORIES, cat=cat,
                               count=count, label=label)

    if cat == "IELTS_BOOK":
        print(f"[ACTIVE] Rendering library_bible.html for IELTS_BOOK")
        chapters = get_bible_chapters()
        return render_template("library_bible.html", cats=CATEGORIES, cat=cat,
                               label=label, chapters=chapters, count=count)

    if cat == "IELTS_SCENE":
        print(f"[ACTIVE] Rendering library_scene.html for IELTS_SCENE")
        return render_template("library_scene.html", cats=CATEGORIES, cat=cat,
                               label=label, sections=SCENE_SECTIONS, count=count)

    return redirect(url_for("library"))


@app.route("/section/<cat>/<section>")
def section_page(cat, section):
    from urllib.parse import unquote
    section = unquote(section)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT subcategory FROM words
        WHERE category=? AND section=? AND subcategory IS NOT NULL AND subcategory!=''
        ORDER BY subcategory
    """, (cat, section))
    subs = [r["subcategory"] for r in cur.fetchall()]
    cur.execute("SELECT COUNT(*) FROM words WHERE category=? AND section=?", (cat, section))
    wc = cur.fetchone()[0]
    conn.close()
    return render_template("section.html", cats=CATEGORIES, cat=cat,
                           section=section, subs=subs, word_count=wc)


@app.route("/words")
def words():
    cat = request.args.get("category", "GRE")
    section = request.args.get("section", "")
    sub = request.args.get("subcategory", "")
    q = request.args.get("q", "").strip()

    conn = get_db()
    cur = conn.cursor()
    subs = []
    if section:
        cur.execute("""
            SELECT DISTINCT subcategory FROM words
            WHERE category=? AND section=? AND subcategory IS NOT NULL AND subcategory!=''
            ORDER BY subcategory
        """, (cat, section))
        subs = [r["subcategory"] for r in cur.fetchall()]
    elif cat:
        cur.execute("""
            SELECT DISTINCT subcategory FROM words
            WHERE category=? AND subcategory IS NOT NULL AND subcategory!=''
            ORDER BY subcategory
        """, (cat,))
        subs = [r["subcategory"] for r in cur.fetchall()]

    where = ["w.category=?"]
    params = [cat]
    if section:
        where.append("w.section=?")
        params.append(section)
    if sub:
        where.append("w.subcategory=?")
        params.append(sub)
    if q:
        where.append("(w.word LIKE ? OR w.meaning_cn LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%"])

    sql = "SELECT w.*,p.is_favorite,p.is_hard FROM words w LEFT JOIN progress p ON w.id=p.word_id WHERE " + " AND ".join(where) + " ORDER BY w.word"
    cur.execute(sql, params)
    words_list = cur.fetchall()
    conn.close()

    return render_template("words.html", words=words_list, cat=cat,
                           section=section, sub=sub, subs=subs, q=q, cats=CATEGORIES)


@app.route("/toggle_favorite/<int:wid>")
def toggle_fav(wid):
    next_url = request.args.get("next") or url_for("index")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT is_favorite FROM progress WHERE word_id=?", (wid,))
    r = cur.fetchone()
    if r:
        cur.execute("UPDATE progress SET is_favorite=? WHERE word_id=?", (0 if r[0] else 1, wid))
    conn.commit()
    conn.close()
    return redirect(next_url)


@app.route("/toggle_hard/<int:wid>")
def toggle_hard(wid):
    next_url = request.args.get("next") or url_for("index")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT is_hard FROM progress WHERE word_id=?", (wid,))
    r = cur.fetchone()
    if r:
        cur.execute("UPDATE progress SET is_hard=? WHERE word_id=?", (0 if r[0] else 1, wid))
    conn.commit()
    conn.close()
    return redirect(next_url)


@app.route("/favorites")
def favorites():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT w.*,p.is_favorite,p.is_hard FROM words w
        JOIN progress p ON w.id=p.word_id
        WHERE p.is_favorite=1 ORDER BY w.category,w.section,w.subcategory,w.word
    """)
    words_list = cur.fetchall()
    conn.close()
    return render_template("favorites.html", words=words_list, cats=CATEGORIES)


@app.route("/hard_words")
def hard_words():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT w.*,p.is_favorite,p.is_hard FROM words w
        JOIN progress p ON w.id=p.word_id
        WHERE p.is_hard=1 ORDER BY w.category,w.section,w.subcategory,w.word
    """)
    words_list = cur.fetchall()
    conn.close()
    return render_template("hard_words.html", words=words_list, cats=CATEGORIES)


@app.route("/method", methods=["GET","POST"])
def method():
    counts = get_counts()
    if request.method == "POST":
        cat = request.form.get("category","GRE")
        days = int(request.form.get("cycle_days",5))
        dayn = int(request.form.get("day_number",1))
        return redirect(url_for("plan", category=cat, cycle_days=days, day_number=dayn))
    return render_template("method.html", counts=counts, cats=CATEGORIES)


@app.route("/plan")
def plan():
    cat = request.args.get("category","GRE")
    days = int(request.args.get("cycle_days",5))
    dayn = int(request.args.get("day_number",1))
    dayn = max(1, min(dayn, days))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT w.*,p.is_favorite,p.is_hard FROM words w LEFT JOIN progress p ON w.id=p.word_id WHERE w.category=? ORDER BY w.id", (cat,))
    all_w = cur.fetchall()
    total = len(all_w)
    per_day = math.ceil(total / days) if total > 0 else 0
    start = (dayn-1)*per_day
    end = min(start+per_day, total)
    today = all_w[start:end] if total > 0 else []

    cur.execute("SELECT w.*,p.is_favorite,p.is_hard FROM words w JOIN progress p ON w.id=p.word_id WHERE p.is_hard=1 AND w.category=? ORDER BY w.word", (cat,))
    hard = cur.fetchall()
    conn.close()

    return render_template("plan.html", words=today, hard=hard,
                           cat=cat, days=days, dayn=dayn,
                           total=total, per_day=per_day,
                           start=start+1, end=end, cats=CATEGORIES)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=False)