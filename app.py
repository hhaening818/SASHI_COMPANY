import os
import sqlite3
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

    conn = sqlite3.connect(DB_PATH)

    c = conn.cursor()

    c.execute("SELECT * FROM portfolio ORDER BY id DESC LIMIT 5")

    images = c.fetchall()

    conn.close()

    return render_template("index.html", images=images)

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