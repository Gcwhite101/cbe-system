from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- COURSE LIST ----------------
courses = [
    {"code": "PHY101", "title": "General Physics I"},
    {"code": "CHM101", "title": "General Chemistry I"},
    {"code": "MTH101", "title": "Calculus I"},
    {"code": "GST101", "title": "Use of English"},
]

# ---------------- DATABASE SETUP ----------------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

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

    c.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student TEXT,
        course TEXT,
        score INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- SEED QUESTIONS ----------------
def seed_questions():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM questions")
    if c.fetchone()[0] == 0:
        questions = [
            ("PHY101", "SI unit of Force is?", "Newton", "Joule", "Pascal", "Watt", "Newton"),
            ("PHY101", "Acceleration due to gravity?", "9.8m/s²", "10m/s²", "8m/s²", "12m/s²", "9.8m/s²"),
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

# ---------------- ROUTES ----------------

# LOGIN
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        session["student"] = request.form["fullname"]
        return redirect("/dashboard")

    return render_template("login.html")


# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "student" not in session:
        return redirect("/")

    student_data = {
        "name": session["student"],
        "matric": "FOS/25/26/123456",
        "department": "Computer Science",
        "faculty": "Computing",
        "level": "100 Level",
        "discipline": "B.Sc Computer Science"
    }

    return render_template("dashboard.html", student=student_data)


# COURSES
@app.route("/courses")
def courses_page():
    if "student" not in session:
        return redirect("/")

    return render_template("course.html", courses=courses)


# EXAM (RETakes ALLOWED)
@app.route("/exam/<course>")
def exam(course):
    if "student" not in session:
        return redirect("/")

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # NO RETAKE BLOCK — ALWAYS LOAD QUESTIONS
    c.execute("SELECT * FROM questions WHERE course=?", (course,))
    questions = c.fetchall()
    conn.close()

    return render_template("exam.html", questions=questions, course=course)


# SUBMIT EXAM
@app.route("/submit_exam/<course>", methods=["POST"])
def submit_exam(course):
    if "student" not in session:
        return redirect("/")

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT * FROM questions WHERE course=?", (course,))
    questions = c.fetchall()

    score = 0
    for q in questions:
        qid = str(q[0])
        correct = q[7]
        if request.form.get(qid) == correct:
            score += 1

    # SAVE EVERY ATTEMPT
    c.execute(
        "INSERT INTO results (student, course, score) VALUES (?, ?, ?)",
        (session["student"], course, score)
    )

    conn.commit()
    conn.close()

    return redirect("/result")


# RESULT PAGE (SHOW ALL ATTEMPTS NEWEST FIRST)
@app.route("/result")
def result_page():
    if "student" not in session:
        return redirect("/")

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("""
        SELECT course, score
        FROM results
        WHERE student=?
        ORDER BY id DESC
    """, (session["student"],))

    results = c.fetchall()
    conn.close()

    return render_template("result.html", results=results)


# GRADES PAGE
@app.route("/grades")
def grades_page():
    if "student" not in session:
        return redirect("/")

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("""
        SELECT course, score
        FROM results
        WHERE student=?
        ORDER BY id DESC
    """, (session["student"],))

    results = c.fetchall()
    conn.close()

    return render_template("grades.html", results=results)


# ADMIN PANEL
@app.route("/admin")
def admin():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT student, course, score FROM results ORDER BY id DESC")
    all_results = c.fetchall()
    conn.close()

    return render_template("admin.html", results=all_results)


# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)