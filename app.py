from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ================= DATABASE =================

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Students table
    c.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matric TEXT UNIQUE,
        fullname TEXT,
        department TEXT,
        password TEXT,
        profile_pic TEXT
    )
    """)

    # Questions table
    c.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course TEXT,
        question TEXT,
        optionA TEXT,
        optionB TEXT,
        optionC TEXT,
        optionD TEXT,
        answer TEXT
    )
    """)

    # Results table
    c.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_matric TEXT,
        course TEXT,
        score INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ================= HOME =================

@app.route("/")
def home():
    return render_template("login.html")

# ================= REGISTER =================

@app.route("/register", methods=["POST"])
def register():
    matric = request.form.get("matric")
    fullname = request.form.get("fullname")
    department = request.form.get("department")
    password = request.form.get("password")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    try:
        c.execute("""
        INSERT INTO students (matric, fullname, department, password, profile_pic)
        VALUES (?, ?, ?, ?, ?)
        """, (matric, fullname, department, password, "default.png"))
        conn.commit()
    except:
        conn.close()
        return "Matric number already exists!"

    conn.close()
    return redirect(url_for("home"))

# ================= LOGIN =================

@app.route("/login", methods=["POST"])
def login():
    matric = request.form.get("matric")
    password = request.form.get("password")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM students WHERE matric=? AND password=?", (matric, password))
    student = c.fetchone()
    conn.close()

    if student:
        session["student_id"] = student[0]
        session["matric"] = student[1]
        session["fullname"] = student[2]
        session["department"] = student[3]
        session["profile_pic"] = student[5]
        return redirect(url_for("dashboard"))
    else:
        return "Invalid login details!"

# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():
    if "student_id" not in session:
        return redirect(url_for("home"))

    return render_template("dashboard.html",
                           name=session["fullname"],
                           matric=session["matric"],
                           department=session["department"],
                           profile=session["profile_pic"])

# ================= PROFILE UPDATE =================

@app.route("/upload", methods=["POST"])
def upload():
    if "student_id" not in session:
        return redirect(url_for("home"))

    file = request.files["profile_pic"]
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("UPDATE students SET profile_pic=? WHERE id=?",
                  (filename, session["student_id"]))
        conn.commit()
        conn.close()

        session["profile_pic"] = filename

    return redirect(url_for("dashboard"))

# ================= COURSES =================

@app.route("/courses")
def courses():
    if "student_id" not in session:
        return redirect(url_for("home"))

    course_list = ["PHY101", "CHM101", "GST101"]
    return render_template("course.html", courses=course_list)

# ================= EXAM =================

@app.route("/exam/<course>")
def exam(course):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM questions WHERE course=?", (course,))
    questions = c.fetchall()
    conn.close()

    return render_template("exam.html", questions=questions, course=course)

# ================= SUBMIT EXAM =================

@app.route("/submit_exam/<course>", methods=["POST"])
def submit_exam(course):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM questions WHERE course=?", (course,))
    questions = c.fetchall()

    score = 0
    for q in questions:
        qid = str(q[0])
        correct = q[7]
        if request.form.get(qid) == correct:
            score += 1

    c.execute("INSERT INTO results (student_matric, course, score) VALUES (?, ?, ?)",
              (session["matric"], course, score))

    conn.commit()
    conn.close()

    return render_template("result.html", score=score, total=len(questions))

# ================= VIEW RESULTS =================

@app.route("/results")
def results():
    if "student_id" not in session:
        return redirect(url_for("home"))

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT course, score FROM results WHERE student_matric=?",
              (session["matric"],))
    student_results = c.fetchall()
    conn.close()

    return render_template("results.html", results=student_results)

# ================= ADMIN PANEL =================

@app.route("/admin")
def admin():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT matric, fullname, department FROM students")
    students = c.fetchall()
    conn.close()

    return render_template("admin.html", students=students)

# ================= LOGOUT =================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)