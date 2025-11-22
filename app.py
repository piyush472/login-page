import os
import mysql.connector as msq 
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for

# 1. Load Environment Variables from the .env file
load_dotenv()

# 2. Database Connection using Environment Variables (Secrets are hidden)
db = msq.connect(
    host=os.getenv("MYSQLHOST"),
    user=os.getenv("MYSQLUSER"),
    password=os.getenv("MYSQLPASSWORD"),
    database=os.getenv("MYSQLDATABASE"),
    port=int(os.getenv("MYSQLPORT"))
)

cursor = db.cursor()

app=Flask(__name__)



@app.route("/" ,methods=["POST","GET"])
def login():
    if request.method=="POST":
        uname=request.form["nm"]
        passwordd=request.form["pwd"]
        cursor.execute("select * from data where username=%s and password=%s",(uname,passwordd))
        result=cursor.fetchone()
        if result:
            return "login successful!"
        else:
            return "invalid usearname or password!"
    return render_template("login.html")


@app.route("/create" ,methods=["GET","POST"])
def create():
    if request.method=="POST":
        uname=request.form["nm"]
        passwordd=request.form["pwd"]
        try:
            cursor.execute("INSERT INTO data (username, password) VALUES (%s, %s)", (uname, passwordd))
            db.commit()
            return "Account created successfully!"

        except:
            return " Username already exists! Choose another one."
    return render_template("create.html")








