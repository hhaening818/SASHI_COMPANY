import os
import sqlite3
import random
from flask import Flask, render_template, request, redirect, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "static/uploads"
DB_PATH = "database.db"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# 카테고리
CATEGORIES = ["apartment", "house", "store"]

# 폴더 생성
for category in CATEGORIES:
    os.makedirs(os.path.join(UPLOAD_FOLDER, category), exist_ok=True)


# DB 초기화 (카테고리 포함)
def init_db():

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS portfolio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        category TEXT,
        description TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

def add_description_column():

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        c.execute("ALTER TABLE portfolio ADD COLUMN description TEXT")
    except:
        pass  # 이미 존재하면 무시

    conn.commit()
    conn.close()

add_description_column()

def add_is_main_column():

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        c.execute("ALTER TABLE portfolio ADD COLUMN is_main INTEGER DEFAULT 0")
    except:
        pass

    conn.commit()
    conn.close()

add_is_main_column()

# 메인
@app.route("/")
def home():

    hero_images = [
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?q=80&w=2070",
        "https://images.unsplash.com/photo-1600607687644-c7171b42498f?q=80&w=2070",
        "https://images.unsplash.com/photo-1600566752355-35792bedcfea?q=80&w=2070",
        "https://images.unsplash.com/photo-1600573472550-8090b5e0745e?q=80&w=2070",
    ]

    hero = random.choice(hero_images)

    return render_template("index.html", hero=hero)


# 시공사례
@app.route("/portfolio")
def portfolio():

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT * FROM portfolio ORDER BY id DESC")

    images = c.fetchall()

    conn.close()

    return render_template("portfolio.html", images=images)


# 관리자 로그인
@app.route("/admin", methods=["GET", "POST"])
def admin():

    if request.method == "POST":

        if request.form["id"] == "admin" and request.form["pw"] == "1234":

            session["admin"] = True

            return redirect("/admin_panel")

    return render_template("admin_login.html")


# 관리자 패널
@app.route("/admin_panel", methods=["GET", "POST"])
def admin_panel():

    if not session.get("admin"):
        return redirect("/admin")

    if request.method == "POST":

        file = request.files["file"]
        category = request.form["category"]
        description = request.form.get("description", "")

        if file and category:

            filename = secure_filename(file.filename)

            save_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                category,
                filename
            )

            file.save(save_path)

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()

            c.execute(
            "INSERT INTO portfolio (filename, category, description) VALUES (?, ?, ?)",
            (filename, category, description)
            )

            conn.commit()
            conn.close()

    # 이미지 목록 불러오기
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT * FROM portfolio ORDER BY id DESC")

    images = c.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        images=images,
        categories=CATEGORIES
    )

@app.route("/set_main/<int:id>")
def set_main(id):

    if not session.get("admin"):
        return redirect("/admin")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 기존 대표 해제
    c.execute("UPDATE portfolio SET is_main=0")

    # 새 대표 설정
    c.execute("UPDATE portfolio SET is_main=1 WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin_panel")

# 삭제
@app.route("/delete/<int:id>")
def delete(id):

    if not session.get("admin"):
        return redirect("/admin")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT filename, category FROM portfolio WHERE id=?", (id,))

    file = c.fetchone()

    if file:

        path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            file[1],
            file[0]
        )

        if os.path.exists(path):
            os.remove(path)

        c.execute("DELETE FROM portfolio WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin_panel")

@app.route("/edit_description/<int:id>", methods=["POST"])
def edit_description(id):

    if not session.get("admin"):
        return redirect("/admin")

    description = request.form.get("description", "")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        "UPDATE portfolio SET description=? WHERE id=?",
        (description, id)
    )

    conn.commit()
    conn.close()

    return redirect("/admin_panel")

# 로그아웃
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

# Railway 실행
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)