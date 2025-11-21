
import os
import mysql.connector as msq 
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for

# 1. Load Environment Variables from the .env file
load_dotenv()

# 2. Database Connection using Environment Variables (Secrets are hidden)
db = msq.connect(
    # Get values from your secure .env file
    host=os.getenv("DB_HOST"),        
    user=os.getenv("DB_USER"),        
    password=os.getenv("DB_PASSWORD"), 
    database=os.getenv("DB_DATABASE")
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








if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3306)))