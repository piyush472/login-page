import os
import cv2
import mysql.connector as msq
import mediapipe as mp
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

# ---------------- MEDIAPIPE SETUP ----------------
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

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


# ---------------- VIDEO STREAM ----------------
def generate_frames():

    import time
    prev_time = 0

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        gesture_text = ""

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:

                lm = hand_landmarks.landmark
                fingers = []

                # -------- THUMB --------
                if lm[4].x < lm[3].x:
                    fingers.append(1)
                else:
                    fingers.append(0)
                
                # -------- OTHER FINGERS --------
                tip_ids = [8, 12, 16, 20]

                for tip in tip_ids:
                    if lm[tip].y < lm[tip - 2].y:
                        fingers.append(1)
                    else:
                        fingers.append(0)

                total = sum(fingers)

                # -------- GESTURE LOGIC --------
                if total == 0:
                    gesture_text = "FIST"
                elif total == 5:
                    gesture_text = "OPEN HAND"
                elif total == 1 and fingers[1] == 1:
                    gesture_text = "ONE"
                elif total == 2 and fingers[1] == 1 and fingers[2] == 1:
                    gesture_text = "TWO"
                elif total == 3 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1:
                    gesture_text = "THREE"
                elif total == 4:
                    gesture_text = "FOUR"
                elif fingers[0] == 1 and total == 1 and lm[4].y < lm[3].y:
                    gesture_text = "THUMBS UP"
                elif fingers[0] == 1 and total == 1 and lm[4].y > lm[3].y:
                    gesture_text = "THUMBS DOWN"
                elif fingers[1] == 1 and fingers[4] == 1 and total == 2:
                    gesture_text = "ROCK"
                else:
                    gesture_text = "UNKNOWN"

                # 🔥 COOL NEON LANDMARK STYLE
                mp_draw.draw_landmarks(
    frame,
    hand_landmarks,
    mp_hands.HAND_CONNECTIONS
)

        # ---------------- MODERN TEXT UI ----------------

        if gesture_text != "":

            font = cv2.FONT_HERSHEY_DUPLEX
            scale = 1.2
            thickness = 2

            text_size = cv2.getTextSize(gesture_text, font, scale, thickness)[0]

            x = 30
            y = 80

            # Semi-transparent box
            overlay = frame.copy()
            cv2.rectangle(
                overlay,
                (x - 20, y - 50),
                (x + text_size[0] + 20, y + 20),
                (0, 0, 0),
                -1
            )

            alpha = 0.6
            frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

            # Neon border
            cv2.rectangle(
                frame,
                (x - 20, y - 50),
                (x + text_size[0] + 20, y + 20),
                (0, 255, 255),
                2
            )

            # Shadow
            cv2.putText(
                frame,
                gesture_text,
                (x + 2, y + 2),
                font,
                scale,
                (0, 0, 0),
                thickness + 2
            )

            # Main text
            cv2.putText(
                frame,
                gesture_text,
                (x, y),
                font,
                scale,
                (0, 255, 255),
                thickness
            )

        # ---------------- FPS COUNTER ----------------
        current_time = time.time()
        fps = 1 / (current_time - prev_time) if prev_time != 0 else 0
        prev_time = current_time

        cv2.putText(
            frame,
            f'FPS: {int(fps)}',
            (10, frame.shape[0] - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
@app.route('/video_feed')
def video_feed():
    if "user" not in session:
        return redirect(url_for("login"))

    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


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


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(debug=True)
