# ============================================================
# SMART ATTENDANCE - ABSENT EMPLOYEE WHATSAPP ALERT
# ============================================================
# ✔ Reads employees from Firebase
# ✔ Checks today's attendance
# ✔ Sends WhatsApp message to absent employees
# ✔ Runs ONE TIME and exits
# ============================================================

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import pywhatkit

# ============================================================
# FIREBASE INITIALIZATION
# ============================================================

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ============================================================
# WHATSAPP MESSAGE FUNCTION
# ============================================================

def send_message(mobile, name, hour, minute):

    message = f"""
Hello {name},

You are marked ABSENT today.

If this is incorrect, please contact HR.

Mahendra Corporation
"""

    print(f"📩 Scheduling message for {name} ({mobile})")

    pywhatkit.sendwhatmsg(
        "+" + str(mobile),   # add country code automatically
        message,
        hour,
        minute,
        wait_time=10,
        tab_close=True,
        close_time=3
    )

# ============================================================
# CHECK ABSENTEES FUNCTION
# ============================================================

def check_absentees():

    print("\n🔎 Checking absent employees...\n")

    today = datetime.now().strftime("%Y-%m-%d")

    # ---------------- FETCH EMPLOYEES ----------------
    employees = []

    for doc in db.collection("employees").stream():

        data = doc.to_dict()

        employees.append({
            "emp_id": doc.id,          # ⭐ document ID = EMP001
            "name": data.get("name"),
            "mobile": data.get("mobile")
        })

    print("Total Employees:", len(employees))

    # ---------------- FETCH TODAY ATTENDANCE ----------------
    attendance_docs = db.collection("attendance") \
        .where("date", "==", today).stream()

    present_ids = []

    for doc in attendance_docs:
        record = doc.to_dict()

        if "emp_id" in record:
            present_ids.append(record["emp_id"])

    print("Present Employees:", len(present_ids))

    # ---------------- FIND ABSENTEES ----------------
    absent_list = []

    for emp in employees:

        if not emp["mobile"]:
            continue

        if emp["emp_id"] not in present_ids:
            absent_list.append(emp)

    print("🚫 Total Absent Employees:", len(absent_list))

    if len(absent_list) == 0:
        print("✅ No absentees today")
        return

    # ---------------- MESSAGE SCHEDULE TIME ----------------
    now = datetime.now()

    send_hour = now.hour
    send_minute = now.minute + 2   # WhatsApp preparation time

    print(f"⏰ Messages scheduled at {send_hour}:{send_minute}")

    # ---------------- SEND MESSAGES ----------------
    for emp in absent_list:
        send_message(
            emp["mobile"],
            emp["name"],
            send_hour,
            send_minute
        )

    print("\n✅ All messages scheduled successfully!")

# ============================================================
# PROGRAM START (RUN ONCE ONLY)
# ============================================================

if __name__ == "__main__":
    check_absentees()