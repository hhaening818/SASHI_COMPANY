import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "1234"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ADMIN_ID = "admin"
ADMIN_PW = "1234"

# DB 생성
def init_db():
    conn = sqlite3.connect("database.db")
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
    return render_template("index.html")

# 시공사례
@app.route("/portfolio")
def portfolio():

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM portfolio ORDER BY id DESC")

    images = c.fetchall()

    conn.close()

    return render_template("portfolio.html", images=images)

# 관리자 로그인
@app.route("/admin", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        id = request.form["id"]
        pw = request.form["pw"]

        if id == ADMIN_ID and pw == ADMIN_PW:

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

        if file:

            filename = secure_filename(file.filename)

            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            conn = sqlite3.connect("database.db")
            c = conn.cursor()

            c.execute("INSERT INTO portfolio (filename) VALUES (?)", (filename,))

            conn.commit()
            conn.close()

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM portfolio ORDER BY id DESC")

    images = c.fetchall()

    conn.close()

    return render_template("admin.html", images=images)

# 삭제
@app.route("/delete/<int:id>")
def delete(id):

    if not session.get("admin"):
        return redirect("/admin")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT filename FROM portfolio WHERE id=?", (id,))
    file = c.fetchone()

    if file:

        os.remove(os.path.join(app.config["UPLOAD_FOLDER"], file[0]))

        c.execute("DELETE FROM portfolio WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin_panel")

# 로그아웃
@app.route("/logout")
def logout():

    session.pop("admin", None)

    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)