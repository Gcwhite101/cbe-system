import os
import sqlite3
from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reg_no TEXT UNIQUE,
        fullname TEXT,
        department TEXT,
        password TEXT,
        profile_pic TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


# ================= HOME =================
@app.route("/")
def home():
    return redirect("/login")


# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        reg_no = request.form["reg_no"]
        fullname = request.form["fullname"]
        department = request.form["department"]
        password = generate_password_hash(request.form["password"])

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        try:
            c.execute("""
            INSERT INTO students (reg_no, fullname, department, password)
            VALUES (?, ?, ?, ?)
            """, (reg_no, fullname, department, password))
            conn.commit()
            flash("Registration successful. Please login.")
            return redirect("/login")
        except:
            flash("Registration number already exists.")
        finally:
            conn.close()

    return render_template("register.html")


# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        reg_no = request.form["reg_no"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM students WHERE reg_no = ?", (reg_no,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[4], password):
            session["user_id"] = user[0]
            return redirect("/dashboard")
        else:
            flash("Invalid login details.")

    return render_template("login.html")


# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM students WHERE id = ?", (session["user_id"],))
    user = c.fetchone()
    conn.close()

    return render_template("dashboard.html", user=user)


# ================= SETTINGS =================
@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if request.method == "POST":
        fullname = request.form["fullname"]
        department = request.form["department"]

        profile_pic = request.files.get("profile_pic")

        if profile_pic and profile_pic.filename != "":
            filename = secure_filename(profile_pic.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            profile_pic.save(filepath)

            c.execute("""
            UPDATE students
            SET fullname=?, department=?, profile_pic=?
            WHERE id=?
            """, (fullname, department, filename, session["user_id"]))
        else:
            c.execute("""
            UPDATE students
            SET fullname=?, department=?
            WHERE id=?
            """, (fullname, department, session["user_id"]))

        conn.commit()
        flash("Profile updated successfully.")

    c.execute("SELECT * FROM students WHERE id = ?", (session["user_id"],))
    user = c.fetchone()
    conn.close()

    return render_template("settings.html", user=user)


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= RENDER PORT FIX =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)