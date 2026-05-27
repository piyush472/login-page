import os
import mysql.connector as msq

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, Response
from werkzeug.security import generate_password_hash, check_password_hash

# ---------------- LOAD ENV ----------------
load_dotenv()

# ---------------- DATABASE ----------------
db = msq.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_DATABASE"),
    port=int(os.getenv("DB_PORT"))
)
cursor = db.cursor()

# ---------------- FLASK ----------------
app = Flask(__name__)
app.secret_key = "super_secret_key"


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        uname = request.form["nm"]
        pwd = request.form["pwd"]

        cursor.execute("SELECT password FROM data WHERE username=%s", (uname,))
        user = cursor.fetchone()

        if user and check_password_hash(user[0], pwd):
            session["user"] = uname

            cursor.execute(
                "UPDATE data SET login_count = login_count + 1 WHERE username=%s",
                (uname,)
            )
            db.commit()

            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error)


# ---------------- CREATE ACCOUNT ----------------
@app.route("/create", methods=["GET", "POST"])
def create():
    message = ""
    msg_type = ""

    if request.method == "POST":
        uname = request.form["nm"]
        pwd = request.form["pwd"]

        hashed_pwd = generate_password_hash(pwd)

        try:
            cursor.execute(
                "INSERT INTO data (username, password, login_count, created_at) VALUES (%s, %s, %s, NOW())",
                (uname, hashed_pwd, 0)
            )
            db.commit()

            message = "User created successfully!"
            msg_type = "success"

        except msq.Error:
            message = "Username already exists!"
            msg_type = "error"

    return render_template("create.html", message=message, msg_type=msg_type)


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    cursor.execute(
        "SELECT created_at, login_count FROM data WHERE username=%s",
        (session["user"],)
    )
    user_info = cursor.fetchone()

    return render_template(
        "dash.html",
        username=session["user"],
        created_at=user_info[0],
        login_count=user_info[1]
    )


