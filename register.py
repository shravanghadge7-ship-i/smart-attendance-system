import cv2
import os
import numpy as np
from supabase import create_client

# =========================
# 🔑 SUPABASE CONFIG
# =========================
url = "https://orrohkftvvhqogzvekrt.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9ycm9oa2Z0dnZocW9nenZla3J0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjMzMDc3MiwiZXhwIjoyMDg3OTA2NzcyfQ.iQk9sI6FA7thWAB2eRiGO0b2_5uepfI_RnRuoacnZxU"
supabase = create_client(url, key)

# =========================
# 👤 USER INPUT
# =========================
name = input("Enter Name: ")
emp_id = input("Enter Employee ID (EMP001): ").upper()
password = input("Enter Password: ")
role = input("Enter Role (employee/hr/manager): ").lower()

# =========================
# 💾 SAVE USER TO SUPABASE
# =========================
try:
    supabase.table("users").insert({
        "emp_id": emp_id,
        "name": name,
        "password": password,
        "role": role
    }).execute()
    print("✅ User saved in database")
except Exception as e:
    print("❌ Database Error:", e)

# =========================
# 📁 CREATE DATASET FOLDER
# =========================
dataset_path = "dataset"
person_path = os.path.join(dataset_path, emp_id)

os.makedirs(person_path, exist_ok=True)

# =========================
# 🎥 START CAMERA
# =========================
cam = cv2.VideoCapture(0)

face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

count = 0
print("📸 Capturing face... Look at camera")

while True:
    ret, img = cam.read()
    if not ret:
        print("❌ Camera not working")
        break

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    faces = face_detector.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        count += 1

        face_img = gray[y:y+h, x:x+w]
        file_path = os.path.join(person_path, f"{count}.jpg")

        cv2.imwrite(file_path, face_img)

        cv2.rectangle(img, (x,y), (x+w,y+h), (255,0,0), 2)

    cv2.imshow("Register Face (Press ESC to stop)", img)

    if cv2.waitKey(1) == 27 or count >= 100:
        break

cam.release()
cv2.destroyAllWindows()

print(f"✅ {count} face images captured")

# =========================
# 🤖 TRAIN MODEL
# =========================
print("🔄 Training model...")

recognizer = cv2.face.LBPHFaceRecognizer_create()

faces = []
ids = []

for person in os.listdir(dataset_path):
    person_folder = os.path.join(dataset_path, person)

    if not os.path.isdir(person_folder):
        continue

    try:
        person_id = int(person.replace("EMP", ""))
    except:
        continue

    for img_name in os.listdir(person_folder):
        img_path = os.path.join(person_folder, img_name)

        gray_img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

        if gray_img is None:
            continue

        faces.append(gray_img)
        ids.append(person_id)

# =========================
# TRAIN + SAVE
# =========================
if len(faces) == 0:
    print("❌ No faces found for training")
else:
    recognizer.train(faces, np.array(ids))
    recognizer.save("trainer.yml")
    print("✅ Model trained and saved as trainer.yml")