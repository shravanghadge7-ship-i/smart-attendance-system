import cv2
import os
import pandas as pd

# ===============================
# AUTO EMPLOYEE ID
# ===============================
def generate_emp_id():
    if not os.path.exists("employees.csv"):
        return "EMP001"
    df = pd.read_csv("employees.csv")
    if df.empty:
        return "EMP001"
    last = df.iloc[-1]["EmpID"]
    num = int(last.replace("EMP",""))
    return f"EMP{num+1:03d}"

name = input("Enter Employee Name: ")
department = input("Enter Department: ")

emp_id = generate_emp_id()
print("Generated:", emp_id)

# ===============================
# EMPLOYEE CSV
# ===============================
if not os.path.exists("employees.csv"):
    pd.DataFrame(columns=["EmpID","Name","Department"]).to_csv("employees.csv", index=False)

df = pd.read_csv("employees.csv")
df.loc[len(df)] = [emp_id,name,department]
df.to_csv("employees.csv", index=False)

# ===============================
# LABEL MAP
# ===============================
if not os.path.exists("label_map.csv"):
    pd.DataFrame(columns=["Label","EmpID"]).to_csv("label_map.csv", index=False)

label_df = pd.read_csv("label_map.csv")
label = len(label_df)

label_df.loc[len(label_df)] = [label, emp_id]
label_df.to_csv("label_map.csv", index=False)

# ===============================
# FACE CAPTURE
# ===============================
path = f"dataset/{label}"
os.makedirs(path, exist_ok=True)

cam = cv2.VideoCapture(0)
detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

count = 0
while True:
    ret, frame = cam.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray, 1.3, 5)

    for (x,y,w,h) in faces:
        count += 1
        cv2.imwrite(f"{path}/{count}.jpg", gray[y:y+h, x:x+w])
        cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)

    cv2.imshow("Register", frame)
    if cv2.waitKey(1)==27 or count>=40:
        break

cam.release()
cv2.destroyAllWindows()
print("✅ Registration completed")
