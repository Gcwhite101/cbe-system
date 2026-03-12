from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"


# ---------------------------
# CREATE DATABASE
# ---------------------------
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matric TEXT UNIQUE,
        full_name TEXT,
        department TEXT,
        faculty TEXT,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()


# ---------------------------
# HOME
# ---------------------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------------------
# REGISTER
# ---------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        matric = request.form["matric"]
        full_name = request.form["full_name"]
        department = request.form["department"]
        faculty = request.form["faculty"]
        password = generate_password_hash(request.form["password"])

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        try:
            cursor.execute("""
            INSERT INTO users (matric, full_name, department, faculty, password)
            VALUES (?, ?, ?, ?, ?)
            """, (matric, full_name, department, faculty, password))

            conn.commit()
            conn.close()

            return redirect("/login")

        except:
            conn.close()
            return "Matric number already exists"

    return render_template("register.html")


# ---------------------------
# LOGIN
# ---------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        matric = request.form["matric"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE matric = ?", (matric,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            return redirect("/dashboard")
        else:
            return "Invalid login details"

    return render_template("login.html")


# ---------------------------
# DASHBOARD
# ---------------------------
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],))
    user = cursor.fetchone()
    conn.close()

    if user is None:
        session.clear()
        return redirect("/login")

    return render_template("dashboard.html", user=user)


# ---------------------------
# COURSES
# ---------------------------
@app.route("/courses")
def courses():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("courses.html")


# ---------------------------
# START TEST
# ---------------------------
@app.route("/start-test")
def start_test():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("start_test.html")


# ---------------------------
# RESULTS
# ---------------------------
@app.route("/results")
def results():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("results.html")


# ---------------------------
# STUDY MATERIALS
# ---------------------------
@app.route("/study-materials")
def study_materials():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("study_materials.html")


# ---------------------------
# SETTINGS
# ---------------------------
@app.route("/settings")
def settings():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("settings.html")


# ---------------------------
# LOGOUT
# ---------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)