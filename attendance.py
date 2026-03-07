import cv2
import pandas as pd
from datetime import datetime, time
import pyttsx3
import threading
import firebase_admin
from firebase_admin import credentials, firestore
import os

# ================= SPEECH =================

engine = pyttsx3.init()
engine.setProperty("rate", 150)

def speak(text):
    def run():
        engine.say(text)
        engine.runAndWait()
    threading.Thread(target=run, daemon=True).start()

# ================= FIREBASE =================

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ================= FACE MODEL =================

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("trainer/face_trainer.yml")

label_map = pd.read_csv("label_map.csv")
employees = pd.read_csv("employees.csv")

face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

cam = cv2.VideoCapture(0)

# ================= SETTINGS =================

COOLDOWN = 20
MIN_WORK_SECONDS = 8 * 3600
OFFICE_TIME = time(9, 30)

last_seen = {}

# ✅ NEW: stop multiple marking same day
already_marked = {}

CSV_FILE = "attendance_log.csv"

# ================= CSV INIT =================

if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=[
        "emp_id","name","date",
        "checkin","checkout","status"
    ]).to_csv(CSV_FILE,index=False)

# ================= CSV HELPER =================

def update_csv(emp, name, date, checkin="", checkout="", status=""):

    df = pd.read_csv(CSV_FILE)
    mask = (df.emp_id==emp) & (df.date==date)

    if not mask.any():
        df.loc[len(df)] = [emp,name,date,checkin,checkout,status]
    else:
        if checkout:
            df.loc[mask,"checkout"] = checkout
        df.loc[mask,"status"] = status

    df.to_csv(CSV_FILE,index=False)

# ================= MAIN LOOP =================

while True:

    ret, frame = cam.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=6,
        minSize=(80,80)
    )

    for (x,y,w,h) in faces:

        label, conf = recognizer.predict(gray[y:y+h,x:x+w])

        # Accuracy check
        if conf < 65:

            emp = str(label_map[label_map.Label==label].iloc[0]["EmpID"])
            empdata = employees[employees.EmpID==emp].iloc[0]

            now = datetime.now()
            today = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M:%S")

            # ================= DETECTION CONTROL =================

            # cooldown protection
            if emp in last_seen and (now-last_seen[emp]).seconds < COOLDOWN:
                continue

            # stop detection after completed
            if emp in already_marked and already_marked[emp] == today:
                continue

            last_seen[emp] = now

            # ================= FIREBASE CHECK =================

            docs = db.collection("attendance") \
                .where("emp_id","==",emp) \
                .where("date","==",today) \
                .stream()

            records = list(docs)

            # ================= CHECK-IN =================
            if not records:

                status = "Late" if now.time()>OFFICE_TIME else "On Time"

                db.collection("attendance").add({
                    "emp_id": emp,
                    "name": empdata.Name,
                    "department": empdata.Department,
                    "date": today,
                    "checkin": current_time,
                    "checkout": "",
                    "status": status,
                    "timestamp": firestore.SERVER_TIMESTAMP
                })

                update_csv(emp, empdata.Name, today,
                           checkin=current_time,
                           status=status)

                speak(empdata.Name + " checked in")

            # ================= CHECK-OUT =================
            else:

                doc = records[0]
                data = doc.to_dict()

                if data["checkout"] == "":

                    checkin_time = datetime.strptime(
                        data["checkin"], "%H:%M:%S"
                    )

                    checkin_datetime = now.replace(
                        hour=checkin_time.hour,
                        minute=checkin_time.minute,
                        second=checkin_time.second
                    )

                    worked_seconds = (now - checkin_datetime).seconds

                    # allow checkout after 8 hours
                    if worked_seconds >= MIN_WORK_SECONDS:

                        db.collection("attendance") \
                          .document(doc.id) \
                          .update({
                              "checkout": current_time,
                              "status": "Completed"
                          })

                        update_csv(emp, empdata.Name, today,
                                   checkout=current_time,
                                   status="Completed")

                        # ✅ LOCK EMPLOYEE FOR TODAY
                        already_marked[emp] = today

                        speak(empdata.Name + " checked out")

            # ================= UI DRAW =================

            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,180,0),2)
            cv2.putText(frame, empdata.Name,(x,y-10),
                        cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,180,0),2)

    cv2.imshow("Smart Attendance System",frame)

    if cv2.waitKey(1)==27:
        break

cam.release()
cv2.destroyAllWindows()