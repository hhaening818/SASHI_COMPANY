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

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# DB 초기화
def init_db():

    conn = sqlite3.connect(DB_PATH)

    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

# 메인
@app.route("/")
def home():

    hero_images = [
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?q=80&w=2070",
    "https://images.unsplash.com/photo-1600607687644-c7171b42498f?q=80&w=2070",
    "https://images.unsplash.com/photo-1600566752355-35792bedcfea?q=80&w=2070",
    "https://images.unsplash.com/photo-1600573472550-8090b5e0745e?q=80&w=2070",
    "https://images.unsplash.com/photo-1600585154526-990dced4db0d?q=80&w=2070",
    "https://images.unsplash.com/photo-1600210492493-0946911123ea?q=80&w=2070",
    "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?q=80&w=2070",
    "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?q=80&w=2070",
    "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?q=80&w=2070",
    "https://images.unsplash.com/photo-1600047509358-9dc75507daeb?q=80&w=2070",
    "https://images.unsplash.com/photo-1600607688969-a5bfcd646154?q=80&w=2070",
    "https://images.unsplash.com/photo-1600607687645-9c9e8f9d0c06?q=80&w=2070",
    "https://images.unsplash.com/photo-1600607687930-6b3f3f7e7b0f?q=80&w=2070",
    "https://images.unsplash.com/photo-1600607688960-e095ff83135f?q=80&w=2070",
    "https://images.unsplash.com/photo-1600607687927-48c1c1f4e5d1?q=80&w=2070",
    "https://images.unsplash.com/photo-1600573472591-ee6b68d14c68?q=80&w=2070",
    "https://images.unsplash.com/photo-1600607688960-8f3e35d5b2c1?q=80&w=2070",
    "https://images.unsplash.com/photo-1600607687643-c7171b42498f?q=80&w=2070",
    "https://images.unsplash.com/photo-1600607687923-26c3f8c5e8d7?q=80&w=2070",
    "https://images.unsplash.com/photo-1600047509782-20d39509f26d?q=80&w=2070"
]

    # 안전 처리
    hero = random.choice(hero_images) if hero_images else hero_images[0]

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

        files = request.files.getlist("file")

        for file in files:

            if file:

                filename = secure_filename(file.filename)

                path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

                file.save(path)

                conn = sqlite3.connect(DB_PATH)

                c = conn.cursor()

                c.execute(
                    "INSERT INTO portfolio (filename) VALUES (?)",
                    (filename,)
                )

                conn.commit()
                conn.close()

    return render_template("admin.html", images=images)

# 삭제
@app.route("/delete/<int:id>")
def delete(id):

    if not session.get("admin"):
        return redirect("/admin")

    conn = sqlite3.connect(DB_PATH)

    c = conn.cursor()

    c.execute("SELECT filename FROM portfolio WHERE id=?", (id,))

    file = c.fetchone()

    if file:

        path = os.path.join(app.config["UPLOAD_FOLDER"], file[0])

        if os.path.exists(path):
            os.remove(path)

        c.execute("DELETE FROM portfolio WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin_panel")

# 로그아웃
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

# Railway용 실행
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)