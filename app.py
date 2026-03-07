from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- FILE UPLOAD CONFIG ----------------
UPLOAD_FOLDER = "static/profile_pics"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------------- DATABASE SETUP ----------------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # STUDENTS TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT,
        matric TEXT UNIQUE,
        department TEXT,
        faculty TEXT,
        password TEXT,
        profile_pic TEXT
    )
    """)

    # QUESTIONS TABLE
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

    # RESULTS TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        course TEXT,
        score INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- SAMPLE QUESTIONS ----------------
def seed_questions():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM questions")
    if c.fetchone()[0] == 0:
        questions = [
            ("PHY101", "SI unit of Force is?", "Newton", "Joule", "Pascal", "Watt", "Newton"),
            ("CHM101", "Atomic number of Oxygen?", "6", "7", "8", "9", "8"),
            ("GST101", "Synonym of Exquisite?", "Beautiful", "Ugly", "Bad", "Small", "Beautiful")
        ]

        c.executemany("""
        INSERT INTO questions (course, question, optionA, optionB, optionC, optionD, answer)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, questions)

    conn.commit()
    conn.close()

seed_questions()

# ---------------- HOME ----------------
@app.route("/")
def home():
    return redirect("/login")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form["fullname"]
        matric = request.form["matric"]
        department = request.form["department"]
        faculty = request.form["faculty"]
        password = generate_password_hash(request.form["password"])

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        try:
            c.execute("""
                INSERT INTO students (fullname, matric, department, faculty, password)
                VALUES (?, ?, ?, ?, ?)
            """, (fullname, matric, department, faculty, password))
            conn.commit()
        except:
            conn.close()
            return "Matric number already exists!"

        conn.close()
        return redirect("/login")

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        matric = request.form["matric"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM students WHERE matric=?", (matric,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[5], password):
            session["student_id"] = user[0]
            return redirect("/dashboard")
        else:
            return "Invalid credentials"

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "student_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM students WHERE id=?", (session["student_id"],))
    student = c.fetchone()
    conn.close()

    return render_template("dashboard.html", student=student)

# ---------------- SETTINGS ----------------
@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "student_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if request.method == "POST":
        file = request.files["profile_pic"]
        if file and file.filename != "":
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            c.execute("UPDATE students SET profile_pic=? WHERE id=?",
                      (filename, session["student_id"]))
            conn.commit()

    c.execute("SELECT * FROM students WHERE id=?", (session["student_id"],))
    student = c.fetchone()
    conn.close()

    return render_template("settings.html", student=student)

# ---------------- EXAM ----------------
@app.route("/exam/<course>")
def exam(course):
    if "student_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM questions WHERE course=?", (course,))
    questions = c.fetchall()
    conn.close()

    return render_template("exam.html", questions=questions, course=course)

# ---------------- SUBMIT EXAM ----------------
@app.route("/submit_exam/<course>", methods=["POST"])
def submit_exam(course):
    if "student_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM questions WHERE course=?", (course,))
    questions = c.fetchall()

    score = 0
    for q in questions:
        qid = str(q[0])
        if request.form.get(qid) == q[7]:
            score += 1

    c.execute("""
        INSERT INTO results (student_id, course, score)
        VALUES (?, ?, ?)
    """, (session["student_id"], course, score))

    conn.commit()
    conn.close()

    return redirect("/results")

# ---------------- RESULTS ----------------
@app.route("/results")
def results():
    if "student_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        SELECT course, score
        FROM results
        WHERE student_id=?
        ORDER BY id DESC
    """, (session["student_id"],))
    results = c.fetchall()
    conn.close()

    return render_template("result.html", results=results)

# ---------------- ADMIN ----------------
@app.route("/admin")
def admin():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        SELECT students.fullname, students.matric, results.course, results.score
        FROM results
        JOIN students ON students.id = results.student_id
        ORDER BY results.id DESC
    """)
    data = c.fetchall()
    conn.close()

    return render_template("admin.html", results=data)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)