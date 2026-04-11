import cv2
import numpy as np
from datetime import datetime
from supabase import create_client
import pyttsx3

# =========================
# 🔑 SUPABASE CONFIG
# =========================
url = "https://orrohkftvvhqogzvekrt.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9ycm9oa2Z0dnZocW9nenZla3J0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjMzMDc3MiwiZXhwIjoyMDg3OTA2NzcyfQ.iQk9sI6FA7thWAB2eRiGO0b2_5uepfI_RnRuoacnZxU"
supabase = create_client(url, key)

# =========================
# 🔊 TEXT TO SPEECH
# =========================
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 1.0)

def speak(text):
    engine.say(text)
    engine.runAndWait()

# =========================
# 📥 LOAD USERS FROM DB
# =========================
res = supabase.table("users").select("*").execute()
users = res.data

name_map = {}

for u in users:
    name_map[u["emp_id"]] = u.get("name", u["emp_id"])

# =========================
# 🤖 LOAD FACE MODEL
# =========================
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("trainer.yml")

face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# =========================
# 🎥 START CAMERA
# =========================
cam = cv2.VideoCapture(0)

print("📸 Attendance started... Press ESC to exit")

while True:
    ret, img = cam.read()
    if not ret:
        break

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_detector.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        id, confidence = recognizer.predict(gray[y:y+h, x:x+w])

        # =========================
        # ✅ FACE MATCH (HIGH ACCURACY)
        # =========================
        if confidence < 60:
            emp_id = f"EMP{id:03d}"
            name = name_map.get(emp_id, emp_id)

            print(f"✅ Recognized: {name} ({emp_id})")

            today = datetime.now().strftime("%Y-%m-%d")
            now_time = datetime.now().strftime("%H:%M:%S")

            # =========================
            # 🔍 CHECK ATTENDANCE
            # =========================
            res = supabase.table("attendance")\
                .select("*")\
                .eq("emp_id", emp_id)\
                .eq("date", today)\
                .execute()

            # =========================
            # 🟢 CHECK-IN
            # =========================
            if len(res.data) == 0:
                supabase.table("attendance").insert({
                    "emp_id": emp_id,
                    "date": today,
                    "checkin": now_time,
                    "status": "Present"
                }).execute()

                print("🟢 Check-in marked")
                speak(f"Welcome {name}, check in successful")

            # =========================
            # 🔴 CHECK-OUT
            # =========================
            else:
                record = res.data[0]

                if record["checkout"] is None:
                    supabase.table("attendance")\
                        .update({
                            "checkout": now_time
                        })\
                        .eq("id", record["id"])\
                        .execute()

                    print("🔴 Check-out marked")
                    speak(f"Goodbye {name}, check out successful")

                else:
                    print("⚠ Already checked out")
                    speak(f"{name}, attendance already completed")

            # =========================
            # EXIT AFTER SUCCESS
            # =========================
            cam.release()
            cv2.destroyAllWindows()
            exit()

    # =========================
    # 🖥️ SHOW CAMERA
    # =========================
    cv2.imshow("Attendance System", img)

    if cv2.waitKey(1) == 27:  # ESC key
        break

cam.release()
cv2.destroyAllWindows()