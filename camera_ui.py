import cv2
import pandas as pd
from datetime import datetime, timedelta
import os

ATTENDANCE_FILE = "Attendance/attendance.csv"
os.makedirs("Attendance", exist_ok=True)

if not os.path.exists(ATTENDANCE_FILE):
    with open(ATTENDANCE_FILE, "w") as f:
        f.write("EmpID,Name,Department,Date,CheckIn,CheckOut,Status\n")

# Load models
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("trainer/face_trainer.yml")

label_map = pd.read_csv("label_map.csv")
employees = pd.read_csv("employees.csv")

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

cam = cv2.VideoCapture(0)

while True:
    ret, frame = cam.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        label, conf = recognizer.predict(gray[y:y+h, x:x+w])

        if conf < 60:
            emp_id = label_map[label_map.Label == label].iloc[0]["EmpID"]
            emp = employees[employees.EmpID == emp_id].iloc[0]

            now = datetime.now()
            date = now.strftime("%Y-%m-%d")
            time_now = now.strftime("%H:%M:%S")

            df = pd.read_csv(ATTENDANCE_FILE)
            today = df[(df.EmpID == emp_id) & (df.Date == date)]

            # ---------- CHECK-IN ----------
            if today.empty:
                df.loc[len(df)] = [
                    emp_id,
                    emp.Name,
                    emp.Department,
                    date,
                    time_now,
                    "",
                    "Present"
                ]
                df.to_csv(ATTENDANCE_FILE, index=False)
                status = "Checked In"

            # ---------- AUTO CHECK-OUT ----------
            else:
                checkin_time = datetime.strptime(today.iloc[0]["CheckIn"], "%H:%M:%S")
                if today.iloc[0]["CheckOut"] == "":
                    if datetime.now() - checkin_time > timedelta(hours=6):
                        df.loc[today.index[0], "CheckOut"] = time_now
                        df.to_csv(ATTENDANCE_FILE, index=False)
                        status = "Checked Out"
                    else:
                        status = "Already In"
                else:
                    status = "Completed"

            cv2.putText(frame, f"{emp_id} | {status}",
                        (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
        else:
            cv2.putText(frame, "Unknown",
                        (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

        cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)

    cv2.imshow("Face Attendance System", frame)

    if cv2.waitKey(1) == 27:  # ESC
        break

cam.release()
cv2.destroyAllWindows()
