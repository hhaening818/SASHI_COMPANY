import os
import sqlite3
import random
from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
def get_kst_time():
    return datetime.utcnow() + timedelta(hours=9)

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

def add_created_at_column():

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        c.execute("ALTER TABLE portfolio ADD COLUMN created_at DATETIME")
    except:
        pass

    conn.commit()
    conn.close()

add_created_at_column()

def init_contact_db():

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS contact (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

init_contact_db()

# 메인
@app.route("/")
def home():

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT filename, category FROM portfolio WHERE is_main=1 LIMIT 1")

    result = c.fetchone()

    conn.close()

    if result:

        hero = url_for(
            "static",
            filename="uploads/" + result[1] + "/" + result[0]
        )

    else:

        hero = "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?q=80&w=2070"

    return render_template("index.html", hero=hero)

@app.route("/kakao_click")
def kakao_click():

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        "INSERT INTO contact (name, phone, message) VALUES (?, ?, ?)",
        ("카카오문의", "-", "카카오톡 문의 클릭")
    )

    conn.commit()
    conn.close()

    return "", 204

# 시공사례
@app.route("/portfolio")
def portfolio():

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT * FROM portfolio ORDER BY id DESC")

    images = c.fetchall()

    conn.close()

    return render_template("portfolio.html", images=images)

# 문의
@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":

        name = request.form["name"]
        phone = request.form["phone"]
        message = request.form["message"]

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        kst_time = datetime.utcnow() + timedelta(hours=9)

        c.execute(
        "INSERT INTO contact (name, phone, message, created_at) VALUES (?, ?, ?, ?)",
        (name, phone, message, kst_time)
        )

        conn.commit()
        conn.close()

        return redirect("/contact?success=1")

    return render_template("contact.html")

# 관리자 로그인
@app.route("/gunjin_admin_7137", methods=["GET", "POST"])
def admin():

    if "login_attempts" not in session:
        session["login_attempts"] = 0

    error = None

    if request.method == "POST":

        # 5회 이상 실패 시 차단
        if session["login_attempts"] >= 5:
            error = "로그인 5회 실패. 브라우저를 새로고침 후 다시 시도하세요."
            return render_template("admin_login.html", error=error)

        admin_id = "gunjin7137"
        admin_pw = "GunJin!7137"

        if request.form["id"] == admin_id and request.form["pw"] == admin_pw:

            session["admin"] = True

            session["login_attempts"] = 0  # 성공 시 초기화

            return redirect("/admin_panel")

        else:

            session["login_attempts"] += 1

            remaining = 5 - session["login_attempts"]

            error = f"로그인 실패. 남은 시도 횟수: {remaining}"

    return render_template("admin_login.html", error=error)

# 관리자 패널
@app.route("/admin_panel", methods=["GET", "POST"])
def admin_panel():

    if not session.get("admin"):
        return redirect("/gunjin_admin_7137")

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

            kst_time = get_kst_time()

            c.execute(
            "INSERT INTO portfolio (filename, category, description, created_at) VALUES (?, ?, ?, ?)",
            (filename, category, description, kst_time)
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
        return redirect("/gunjin_admin_7137")

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
        return redirect("/gunjin_admin_7137")

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
        return redirect("/gunjin_admin_7137")

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

# 관리자 문의 관리
@app.route("/admin_contacts")
def admin_contacts():

    if not session.get("admin"):
        return redirect("/gunjin_admin_7137")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT * FROM contact ORDER BY id DESC")

    contacts = c.fetchall()

    conn.close()

    return render_template("admin_contacts.html", contacts=contacts)

# Railway 실행
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)