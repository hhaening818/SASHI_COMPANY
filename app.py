import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

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

# 시공사례 페이지
@app.route("/portfolio")
def portfolio():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT filename FROM portfolio ORDER BY id DESC")
    images = c.fetchall()
    conn.close()

    return render_template("portfolio.html", images=images)

# 관리자 페이지
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":

        file = request.files["file"]

        if file:
            filename = secure_filename(file.filename)

            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

            file.save(filepath)

            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            c.execute("INSERT INTO portfolio (filename) VALUES (?)", (filename,))
            conn.commit()
            conn.close()

            return redirect("/portfolio")

    return render_template("admin.html")

if __name__ == "__main__":
    app.run(debug=True)