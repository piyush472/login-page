import os
import mysql.connector as msq
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session

# For password hashing
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables
load_dotenv()

# Database connection
db = msq.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_DATABASE"),
    port=int(os.getenv("DB_PORT"))
)
cursor = db.cursor()

app = Flask(__name__)
app.secret_key = "super_secret_key"   # REQUIRED for sessions


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        uname = request.form["nm"]
        pwd = request.form["pwd"]

        # Get hashed password from DB
        cursor.execute("SELECT password FROM data WHERE username=%s", (uname,))
        user = cursor.fetchone()

        if user and check_password_hash(user[0], pwd):
            session["user"] = uname

            # Increment login count
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
    message = ""          # variable to hold message
    msg_type = ""         # "success" or "error" for styling

    if request.method == "POST":
        uname = request.form["nm"]
        pwd = request.form["pwd"]

        # Hash the password before storing
        hashed_pwd = generate_password_hash(pwd, method='pbkdf2:sha256')

        try:
            cursor.execute(
                "INSERT INTO data (username, password, login_count, created_at) VALUES (%s, %s, %s, NOW())",
                (uname, hashed_pwd, 0)
            )
            db.commit()
            message = "User created successfully! Redirecting to login..."
            msg_type = "success"
            return render_template("create.html", message=message, msg_type=msg_type, redirect_login=True)
        except msq.Error:
            message = "Username already exists!"
            msg_type = "error"
            return render_template("create.html", message=message, msg_type=msg_type)

    return render_template("create.html", message=message, msg_type=msg_type)


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    # Get created_at and login_count
    cursor.execute(
        "SELECT created_at, login_count FROM data WHERE username=%s",
        (session["user"],)
    )
    user_info = cursor.fetchone()  # returns (created_at, login_count)

    return render_template(
        "dash.html",
        username=session["user"],
        created_at=user_info[0],
        login_count=user_info[1]
    )


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


# ---------------- ABOUT ----------------
@app.route("/aboutus")
def about():
    return render_template("about.html")


# ---------------- CONTACT ----------------
@app.route("/contactus")
def contact():
    return render_template("contactus.html")


if __name__ == "__main__":
    app.run(debug=True)
