import os
import sqlite3
import random
from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from flask import send_from_directory
def get_kst_time():
    return datetime.utcnow() + timedelta(hours=9)

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "/data/uploads"
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

def add_region_column():

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        c.execute("ALTER TABLE contact ADD COLUMN region TEXT")
    except:
        pass

    conn.commit()
    conn.close()

add_region_column()

# 메인
import random

@app.route("/")
def home():

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    hero_images = []

    # 1️⃣ 대표사진 1장
    c.execute("""
        SELECT filename, category
        FROM portfolio
        WHERE is_main=1
        LIMIT 1
    """)

    main = c.fetchone()

    if main:

        hero_images.append(
            "/uploads/" + row[1] + "/" + row[0]
        )


    # 2️⃣ 최근 시공사례 4장
    c.execute("""
        SELECT filename, category
        FROM portfolio
        ORDER BY created_at DESC
        LIMIT 4
    """)

    rows = c.fetchall()

    for row in rows:

        hero_images.append(
            url_for(
                "static",
                filename="uploads/" + row[1] + "/" + row[0]
            )
        )


    # 3️⃣ 웹 이미지 5장
    web_images = [
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c",
        "https://images.unsplash.com/photo-1600573472550-8090b5e0745e",
        "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c",
        "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea",
        "https://images.unsplash.com/photo-1600607687644-c7171b42498f"
    ]

    hero_images.extend(web_images)


    # ⭐ 핵심: 순서 랜덤 섞기
    random.shuffle(hero_images)

    hero = hero_images[0] if hero_images else None

    conn.close()


    # 슬라이드용 시공사례
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT filename, category
        FROM portfolio
        ORDER BY created_at DESC
    """)

    rows = c.fetchall()

    conn.close()

    slide_images = []

    for row in rows:

        slide_images.append({
            "filename": row[0],
            "category": row[1]
        })


    return render_template(
        "index.html",
        hero_images=hero_images,
        hero=hero,
        construction_images=slide_images
    )

@app.template_filter("kst")
def format_kst(datetime_str):

    if not datetime_str:
        return ""

    dt = str(datetime_str)

    year = dt[0:4]
    month = dt[5:7]
    day = dt[8:10]
    hour = dt[11:13]
    minute = dt[14:16]

    return f"{year}년 {month}월 {day}일 {hour}:{minute}"

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

        sido = request.form["sido"]
        sigungu = request.form["sigungu"]

        region = f"{sido} {sigungu}"

        message = request.form["message"]

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute(
        "INSERT INTO contact (name, phone, region, message) VALUES (?, ?, ?, ?)",
        (name, phone, region, message)
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

        cropped = request.form.get("cropped_image")
        category = request.form["category"]
        description = request.form.get("description", "")

        # Cropper로 자른 이미지 저장
        if cropped and category:

            import base64
            import time

            header, data = cropped.split(",")

            filename = f"crop_{int(time.time())}.jpg"

            save_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                category,
                filename
            )

            with open(save_path, "wb") as f:
                f.write(base64.b64decode(data))

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()

            kst_time = get_kst_time()

            c.execute(
                """
                INSERT INTO portfolio
                (filename, category, description, created_at)
                VALUES (?, ?, ?, ?)
                """,
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

    region = request.args.get("region")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ⭐ 문의 목록 가져오기 (필터 적용)
    if region:
        c.execute(
        "SELECT * FROM contact WHERE region LIKE ? ORDER BY id DESC",
        (region + "%",)
        )
    else:
        c.execute("SELECT * FROM contact ORDER BY id DESC")

    contacts = c.fetchall()

    # ⭐ 지역별 통계 가져오기 (전체 기준)
    c.execute("""
    SELECT SUBSTR(region, 1, INSTR(region, ' ') - 1) AS sido, COUNT(*)
    FROM contact
    WHERE region IS NOT NULL AND region != ''
    GROUP BY sido
    ORDER BY COUNT(*) DESC
    """)

    region_stats_raw = c.fetchall()

    conn.close()

    total_count = len(contacts)

    # 전체 문의 수 가져오기 (퍼센트 계산용)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM contact")

    total_all = c.fetchone()[0]

    conn.close()

    # ⭐ 퍼센트 계산
    region_stats = []

    for region_name, count in region_stats_raw:

        if total_all > 0:
            percent = round((count / total_all) * 100)
        else:
            percent = 0

        region_stats.append((region_name, count, percent))

    return render_template(
        "admin_contacts.html",
        contacts=contacts,
        total_count=total_count,
        region_stats=region_stats
    )

from flask import send_from_directory

@app.route("/uploads/<category>/<filename>")
def uploaded_file(category, filename):
    return send_from_directory(
        os.path.join("/data/uploads", category),
        filename
    )

# Railway 실행
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)