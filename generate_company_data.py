from supabase import create_client
from datetime import datetime, timedelta
import random

# ================= SUPABASE =================

SUPABASE_URL = "https://orrohkftvvhqogzvekrt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9ycm9oa2Z0dnZocW9nenZla3J0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjMzMDc3MiwiZXhwIjoyMDg3OTA2NzcyfQ.iQk9sI6FA7thWAB2eRiGO0b2_5uepfI_RnRuoacnZxU"


supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

EMP_ID = "EMP002"

# ================= DATE RANGE =================
start_date = datetime(2025, 1, 1)
end_date = datetime(2026, 2, 28)

# ================= CONFIG =================

# 20 Late Days
late_days = [
"2025-01-08","2025-01-29","2025-02-18","2025-03-06","2025-03-27",
"2025-04-14","2025-05-09","2025-05-28","2025-06-19","2025-07-04",
"2025-07-22","2025-08-13","2025-09-02","2025-09-24","2025-10-16",
"2025-11-04","2025-11-26","2025-12-17","2026-01-14","2026-02-09"
]

# 21 Approved Leaves
approved_leaves = [
("2025-01-21","2025-01-22"),
("2025-02-06","2025-02-06"),
("2025-02-26","2025-02-27"),
("2025-03-18","2025-03-19"),
("2025-04-08","2025-04-09"),
("2025-04-29","2025-04-29"),
("2025-05-16","2025-05-17"),
("2025-06-05","2025-06-05"),
("2025-06-24","2025-06-25"),
("2025-07-15","2025-07-16"),
("2025-07-31","2025-07-31"),
("2025-08-18","2025-08-19"),
("2025-09-12","2025-09-13"),
("2025-10-02","2025-10-02"),
("2025-10-28","2025-10-29"),
("2025-11-18","2025-11-19"),
("2025-12-09","2025-12-10"),
("2026-01-07","2026-01-08"),
("2026-01-26","2026-01-26"),
("2026-02-06","2026-02-07"),
("2026-02-19","2026-02-19")
]

# 6 Rejected Leaves (worked days)
rejected_leaves = [
("2025-02-11","2025-02-11"),
("2025-05-21","2025-05-21"),
("2025-07-08","2025-07-08"),
("2025-09-17","2025-09-17"),
("2025-11-03","2025-11-03"),
("2026-01-19","2026-01-19"),
]

# 4 Absent Days
absent_days = [
"2025-03-11",
"2025-08-06",
"2025-12-03",
"2026-02-15"
]

print("🚀 Creating dataset for EMP002...\n")

current = start_date

while current <= end_date:

    date_str = current.strftime("%Y-%m-%d")

    # Skip Sundays
    if current.weekday() == 6:
        current += timedelta(days=1)
        continue

    # ABSENT DAYS
    if date_str in absent_days:
        print("❌ Absent:", date_str)
        current += timedelta(days=1)
        continue

    # APPROVED LEAVES
    leave_flag = False
    for leave in approved_leaves:
        if leave[0] <= date_str <= leave[1]:

            if date_str == leave[0]:
                days_count = (
                    datetime.strptime(leave[1], "%Y-%m-%d")
                    - datetime.strptime(leave[0], "%Y-%m-%d")
                ).days + 1

                supabase.table("leaves").insert({
                    "emp_id": EMP_ID,
                    "from_date": leave[0],
                    "to_date": leave[1],
                    "reason": "Approved Leave",
                    "type": "Full Day",
                    "part": "",
                    "comments": "",
                    "days": days_count,
                    "status": "Approved",
                    "applied_on": datetime.utcnow().isoformat()
                }).execute()

                print("🌴 Approved Leave:", leave[0])

            leave_flag = True

    if leave_flag:
        current += timedelta(days=1)
        continue

    # REJECTED LEAVES (employee worked)
    for leave in rejected_leaves:
        if leave[0] == date_str:

            supabase.table("leaves").insert({
                "emp_id": EMP_ID,
                "from_date": leave[0],
                "to_date": leave[1],
                "reason": "Leave Rejected",
                "type": "Full Day",
                "part": "",
                "comments": "",
                "days": 1,
                "status": "Rejected",
                "applied_on": datetime.utcnow().isoformat()
            }).execute()

            print("🚫 Rejected Leave:", date_str)

    # ATTENDANCE
    if date_str in late_days:
        hour = random.randint(10, 11)
        minute = random.randint(10, 59)
        checkin = f"{hour}:{minute:02}"
        status = "Late"
    else:
        checkin = f"09:{random.randint(0,45):02}"
        status = "Present"

    checkout = f"18:{random.randint(0,30):02}"

    supabase.table("attendance").insert({
        "emp_id": EMP_ID,
        "date": date_str,
        "checkin": checkin,
        "checkout": checkout,
        "status": status
    }).execute()

    print("✅ Attendance:", date_str, status)

    current += timedelta(days=1)

print("\n🎉 EMP002 DATA GENERATED SUCCESSFULLY!")