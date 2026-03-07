from supabase import create_client
from datetime import datetime, timedelta
import random

# ================= SUPABASE =================
SUPABASE_URL = "https://orrohkftvvhqogzvekrt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9ycm9oa2Z0dnZocW9nenZla3J0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjMzMDc3MiwiZXhwIjoyMDg3OTA2NzcyfQ.iQk9sI6FA7thWAB2eRiGO0b2_5uepfI_RnRuoacnZxU"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

EMP_ID = "EMP001"

# ================= DATE RANGE =================
start_date = datetime(2025, 9, 1)
end_date = datetime(2026, 2, 28)

# ================= SPECIAL DAYS =================
late_days = [
    "2025-09-10",
    "2025-10-05",
    "2025-11-12",
    "2025-12-03",
    "2026-01-15",
    "2026-02-10",
]

approved_leaves = [
    ("2025-11-20", "2025-11-21"),
    ("2026-01-05", "2026-01-06"),
]

rejected_leave = ("2025-12-15", "2025-12-15")

absent_day = "2026-02-01"

print("🚀 Generating attendance...")

current = start_date

while current <= end_date:

    date_str = current.strftime("%Y-%m-%d")

    # Skip Sundays
    if current.weekday() == 6:
        current += timedelta(days=1)
        continue

    # ABSENT DAY
    if date_str == absent_day:
        print("❌ Absent:", date_str)
        current += timedelta(days=1)
        continue

    # APPROVED LEAVE CHECK
    leave_flag = False
    for l in approved_leaves:
        if l[0] <= date_str <= l[1]:
            leave_flag = True

            supabase.table("leaves").insert({
                "emp_id": EMP_ID,
                "from_date": l[0],
                "to_date": l[1],
                "reason": "Personal Leave",
                "days": 2,
                "status": "Approved",
                "applied_on": datetime.utcnow().isoformat()
            }).execute()

    if leave_flag:
        print("🌴 Leave:", date_str)
        current += timedelta(days=1)
        continue

    # REJECTED LEAVE (employee still works)
    if rejected_leave[0] <= date_str <= rejected_leave[1]:

        supabase.table("leaves").insert({
            "emp_id": EMP_ID,
            "from_date": rejected_leave[0],
            "to_date": rejected_leave[1],
            "reason": "Rejected Leave",
            "days": 1,
            "status": "Rejected",
            "applied_on": datetime.utcnow().isoformat()
        }).execute()

    # LATE DAYS
    if date_str in late_days:
        check_in = "10:10"
        status = "Late"
    else:
        check_in = f"09:{random.randint(0,45):02}"
        status = "Present"

    check_out = f"18:{random.randint(0,30):02}"

    # INSERT ATTENDANCE
    supabase.table("attendance").insert({
        "emp_id": EMP_ID,
        "date": date_str,
        "check_in": check_in,
        "check_out": check_out,
        "status": status
    }).execute()

    print("✅ Added:", date_str, status)

    current += timedelta(days=1)

print("🎉 DATA GENERATION COMPLETE")