from flask import Flask,request,jsonify,render_template,redirect,session
from datetime import datetime
import re
import os

# 🔕 HIDE TENSORFLOW WARNINGS
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import base64
import cv2
from deepface import DeepFace
import numpy as np
import requests

app = Flask(__name__)
app.secret_key = "smartattendance"

# ✅ GLOBAL ERROR HANDLER
@app.errorhandler(Exception)
def handle_exception(e):
    print("ERROR:", e)
    return jsonify({"error": str(e)}), 500
# ================= SUPABASE SAFE CLIENT =================
from supabase import create_client
from supabase.lib.client_options import ClientOptions
import httpx

SUPABASE_URL = "https://orrohkftvvhqogzvekrt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9ycm9oa2Z0dnZocW9nenZla3J0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjMzMDc3MiwiZXhwIjoyMDg3OTA2NzcyfQ.iQk9sI6FA7thWAB2eRiGO0b2_5uepfI_RnRuoacnZxU"


supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

# ================= SUPABASE HELPER =================

def get_one(table, column, value):
    res = supabase.table(table).select("*").eq(column, value).execute()
    return res.data[0] if res.data else None

def get_all(table, column=None, value=None):
    query = supabase.table(table).select("*")
    if column:
        query = query.eq(column, value)
    return query.execute().data

def insert_data(table, data):
    try:
        res = supabase.table(table).insert(data).execute()

        if hasattr(res, "error") and res.error:
            print("SUPABASE INSERT ERROR:", res.error)
            return False

        return True

    except Exception as e:
        print("INSERT ERROR:", e)
        return False

def update_data(table, column, value, data):
    supabase.table(table).update(data).eq(column, value).execute()

def delete_data(table, column, value):
    supabase.table(table).delete().eq(column, value).execute()

# ======================================================
# EMAIL VALIDATION
# ======================================================
def valid_email(email):
    pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern,email)

# ======================================================
# DEFAULT PROFILE STRUCTURE
# ======================================================
def default_profile():
    return {
        "name":"",
        "email":"",
        "mobile":"",
        "department":"",
        "gender":"",
        "dob":"",
        "address":"",
        "father":"",
        "pan":"",
        "aadhaar":"",
        "uan":"",
        "created_at": datetime.utcnow().isoformat()
    }

# ======================================================
# ENSURE PROFILE EXISTS
# ======================================================
def ensure_employee_profile(emp_id):
    if not emp_id:
        return

    emp = get_one("employees", "emp_id", emp_id) or {}

    if not emp:
        data = default_profile()
        data["emp_id"] = emp_id
        insert_data("employees", data)

# ======================================================
# HOME
# ======================================================
@app.route("/")
def home():
    return redirect("/login")


# ======================================================
# KEEP SERVER ALIVE (AUTO PING)
# ======================================================
@app.route("/ping")
def ping():
    return "Server is running"

# ======================================================
# LOGIN
# ======================================================
@app.route("/login",methods=["GET","POST"])
def login():

    if request.method=="POST":

        emp_id=request.form["emp_id"]
        password=request.form["password"]

        user = get_one("users", "emp_id", emp_id)

        if user and str(user.get("password")) == str(password):

            ensure_employee_profile(emp_id)
            emp = get_one("employees", "emp_id", emp_id)

            session["emp_id"]=emp_id
            session["role"]=user["role"]
            session["name"]=emp.get("name","Employee") if emp else "Employee"
            session["photo"]=user.get("photo","https://via.placeholder.com/100")

            return redirect("/"+session["role"])

    return render_template("login.html")

# ======================================================
# PROFILE APIs
# ======================================================
@app.route("/profile")
def profile():

    emp_id=session.get("emp_id")
    ensure_employee_profile(emp_id)
    data = get_one("employees", "emp_id", emp_id)

    return jsonify({
        "emp_id":emp_id,
        "name":data.get("name",""),
        "email":data.get("email",""),
        "mobile":data.get("mobile",""),
        "department":data.get("department",""),
        "photo":session.get("photo")
    })

@app.route("/profile_full")
def profile_full():

    emp_id=session.get("emp_id")
    ensure_employee_profile(emp_id)
    data = get_one("employees", "emp_id", emp_id)

    return jsonify({
        "emp_id":emp_id,
        "name":data.get("name",""),
        "email":data.get("email",""),
        "mobile":data.get("mobile",""),
        "department":data.get("department",""),
        "gender":data.get("gender",""),
        "dob":data.get("dob",""),
        "address":data.get("address",""),
        "father":data.get("father",""),
        "pan":data.get("pan",""),
        "aadhaar":data.get("aadhaar",""),
        "uan":data.get("uan",""),
        "photo":session.get("photo"),

        "face_encoding": data.get("face_encoding")
    })

# ======================================================
# ADMIN PANEL
# ======================================================
@app.route("/admin")
def admin():

    if session.get("role")!="admin":
        return redirect("/login")

    users = get_all("users")
    employees = get_all("employees")

    return render_template("admin.html",users=users,employees=employees)

@app.route("/add_user",methods=["POST"])
def add_user():

    emp_id=request.form["id"]

    insert_data("users", {
        "emp_id": emp_id,
        "password": request.form["password"],
        "role": request.form["role"],
        "photo": "https://via.placeholder.com/100"
    })

    ensure_employee_profile(emp_id)
    return redirect("/admin")

@app.route("/update_employee",methods=["POST"])
def update_employee():

    if session.get("role")!="admin":
        return redirect("/login")

    emp_id=request.form["emp_id"]
    email=request.form.get("email","")

    if email and not valid_email(email):
        return "Invalid Email Format"

    update_values = {
        "name":request.form.get("name",""),
        "email":email,
        "mobile":request.form.get("mobile",""),
        "department":request.form.get("department",""),
        "gender":request.form.get("gender",""),
        "dob":request.form.get("dob",""),
        "address":request.form.get("address",""),
        "father":request.form.get("father",""),
        "updated_at":str(datetime.now())
    }

    update_data("employees", "emp_id", emp_id, update_values)
    return redirect("/admin")

# ======================================================
# EMPLOYEE PAGE
# ======================================================
@app.route("/employee")
def employee():
    if session.get("role")=="employee":
        return render_template("employee.html")
    return redirect("/login")


# ======================================================
# MANAGER PAGE
# ======================================================

@app.route("/manager")
def manager():

    if session.get("role") != "manager":
        return redirect("/login")

    return render_template("manager.html")

# ======================================================
# HR DASHBOARD
# ======================================================
@app.route("/hr")
def hr():

    if session.get("role") != "hr":
        return redirect("/login")

    emp_filter = request.args.get("emp_id")

    docs = supabase.table("leaves") \
        .select("*") \
        .eq("to_id", session.get("emp_id")) \
        .eq("status","Pending") \
        .order("applied_on", desc=True) \
        .execute().data

    leaves=[]
    emp_set=set()

    for l in docs:

        if emp_filter and l.get("emp_id") != emp_filter:
            continue

        leaves.append(l)

        if l.get("emp_id"):
            emp_set.add(l["emp_id"])

    return render_template(
        "hr.html",
        leaves=leaves,
        employees=sorted(emp_set)
    )

@app.route("/hr_notifications")
def hr_notifications():

    docs = supabase.table("leaves") \
        .select("*") \
        .eq("status", "Pending") \
        .eq("to_id", session.get("emp_id")) \
        .execute().data

    return jsonify({"pending": len(docs)})

# ======================================================
# ATTENDANCE API
# ======================================================
@app.route("/attendance")
def attendance_data():
    if not session.get("emp_id"):
        return jsonify([])

    emp_id=session.get("emp_id")

    docs = supabase.table("attendance") \
        .select("*") \
        .eq("emp_id", emp_id) \
        .execute().data

    return jsonify(docs)

# ======================================================
# MANAGER TEAM ATTENDANCE
# ======================================================
@app.route("/team_attendance")
def team_attendance():

    # ❌ block non-manager
    if session.get("role") != "manager":
        return jsonify([])

    manager_id = session.get("emp_id")

    print("Manager ID:", manager_id)

    # ✅ STEP 1: GET TEAM MEMBERS
    team = supabase.table("employees") \
        .select("emp_id,name,manager_id") \
        .eq("manager_id", manager_id) \
        .execute().data

    print("Team Data:", team)

    # ❌ If no team → return empty
    if not team:
        return jsonify([])

    # ✅ STEP 2: GET EMPLOYEE IDS
    emp_ids = [e["emp_id"] for e in team]

    print("Employee IDs:", emp_ids)

    # ✅ STEP 3: GET ATTENDANCE (LATEST FIRST)
    docs = supabase.table("attendance") \
        .select("*") \
        .in_("emp_id", emp_ids) \
        .order("date", desc=True) \
        .execute().data

    print("Attendance Records:", docs)

    # ❌ If no attendance
    if not docs:
        return jsonify([])



    # ✅ STEP 5: FINAL RESPONSE
    result = []

    for a in docs:

        emp = next((e for e in team if e["emp_id"] == a["emp_id"]), None)

        result.append({
            "emp_id": a["emp_id"],
            "name": emp["name"] if emp else "",
            "date": a.get("date"),
            "checkin": a.get("checkin"),
            "checkout": a.get("checkout"),
            "status": a.get("status")
        })

    return jsonify(result)

# ======================================================
# LEAVES API
# ======================================================
@app.route("/leaves")
def leaves_data():
    if not session.get("emp_id"):
        return jsonify([])

    emp_id=session.get("emp_id")
    docs = get_all("leaves", "emp_id", emp_id)

    return jsonify(docs)



# ======================================================
# MANAGER LEAVE REQUESTS
# ======================================================
@app.route("/manager_leave_requests")
def manager_leave_requests():

    if session.get("role") != "manager":
        return jsonify([])

    manager_id = session.get("emp_id")

    response = supabase.table("leaves") \
        .select("*") \
        .eq("to_id", manager_id) \
        .eq("status", "Pending") \
        .order("applied_on", desc=True) \
        .execute()

    return jsonify(response.data if response.data else [])


# ======================================================
# MANAGER APPROVE LEAVE
# ======================================================
@app.route("/manager_approve_leave", methods=["POST"])
def manager_approve_leave():

    if session.get("role") != "manager":
        return jsonify({"status": "unauthorized"})

    data = request.json
    leave_id = data["id"]

    leave = get_one("leaves", "id", leave_id)

    if not leave:
        return jsonify({"status": "not_found"})

    # ✅ GET MANAGER DETAILS (FOR HR ROUTING)
    manager = get_one("employees", "emp_id", session.get("emp_id"))

    # 🔥 UPDATE → SEND TO HR
    update_data("leaves", "id", leave_id, {
        "status": "Manager Approved",
        "to_id": manager.get("hr_id")   # 🔥 IMPORTANT
    })

    # ✅ NOTIFICATION TO EMPLOYEE
    insert_data("notifications", {
        "emp_id": leave["emp_id"],
        "message": "✅ Your leave approved by Manager",
        "read": False,
        "created_at": datetime.utcnow().isoformat()
    })

    return jsonify({"success": True})


# ======================================================
# MANAGER REJECT LEAVE
# ======================================================
@app.route("/manager_reject_leave", methods=["POST"])
def manager_reject_leave():

    if session.get("role") != "manager":
        return jsonify({"status": "unauthorized"})

    data = request.json
    leave_id = data["id"]

    leave = get_one("leaves", "id", leave_id)

    if not leave:
        return jsonify({"status": "not_found"})

    update_data("leaves", "id", leave_id, {
        "status": "Manager Rejected"
    })

    # ✅ NOTIFICATION
    insert_data("notifications", {
        "emp_id": leave["emp_id"],
        "message": "❌ Your leave rejected by Manager",
        "read": False,
        "created_at": datetime.utcnow().isoformat()
    })

    return jsonify({"success": True})
# ======================================================
# YEARLY LEAVE DETAILS
# ======================================================

@app.route("/leave_details")
def leave_details():

    if not session.get("emp_id"):
        return jsonify({})

    emp_id = session.get("emp_id")
    year = request.args.get("year")

    if not year:
        year = str(datetime.now().year)

    TOTAL_LEAVE = 21
    used_days = 0
    leave_list = []

    docs = supabase.table("leaves") \
        .select("*") \
        .eq("emp_id", emp_id) \
        .in_("status", ["Approved","Manager Approved"]) \
        .execute().data

    for data in docs:
        
        from_date = data.get("from_date","")

        if from_date.startswith(year):

            days = int(data.get("days",1))
            used_days += days

            leave_list.append({
                "from": data.get("from_date"),
                "to": data.get("to_date"),
                "days": days,
                "reason": data.get("reason"),
                "status": data.get("status")
            })

    remaining = TOTAL_LEAVE - used_days

    return jsonify({
        "total": TOTAL_LEAVE,
        "used": used_days,
        "remaining": remaining,
        "leaves": leave_list
    })



# ======================================================
# REJECT LEAVE
# ======================================================
@app.route("/reject/<leave_id>",methods=["POST"])
def reject_leave(leave_id):

    if session.get("role")!="hr":
        return redirect("/login")

    reason=request.form["reason"]

    data = get_one("leaves", "id", leave_id)


    if not data:
        return redirect("/hr")

    update_data("leaves", "id", leave_id,
                {"status":"Rejected","hr_reason":reason})

    insert_data("notifications", {
        "emp_id":data["emp_id"],
        "message":"❌ Your leave has been rejected",
        "read":False,
        "created_at": datetime.utcnow().isoformat()
    })

    return redirect("/hr")


# ======================================================
# APPLY LEAVE
# ======================================================
@app.route("/apply_leave", methods=["POST"])
def apply_leave():

    # 🔒 Check login
    if not session.get("emp_id"):
        return jsonify({"status": "error", "message": "Not logged in"})

    try:
        data = request.json
        emp_id = session.get("emp_id")
        role = session.get("role")

        # ===== DATE VALIDATION =====
        start = datetime.strptime(data["from"], "%Y-%m-%d")
        end = datetime.strptime(data["to"], "%Y-%m-%d")

        if end < start:
            return jsonify({"status": "error", "message": "Invalid date range"})

        days = (end - start).days + 1

        # ===== GET EMPLOYEE DETAILS =====
        emp = get_one("employees", "emp_id", emp_id)

        if not emp:
            return jsonify({"status": "error", "message": "Employee not found"})

        # ===== DECIDE APPROVER =====
        to_id = None

        if role == "employee":
            to_id = emp.get("manager_id")

        elif role == "manager":
            to_id = emp.get("hr_id")

        elif role == "hr":
            to_id = emp.get("admin_id")

        else:
            return jsonify({"status": "error", "message": "Invalid role"})

        # 🚨 SAFETY CHECK (IMPORTANT)
        if not to_id:
            return jsonify({
                "status": "error",
                "message": "Approver not assigned (check employees table)"
            })

        # ===== INSERT INTO DATABASE =====
        result = insert_data("leaves", {
            "emp_id": emp_id,
            "to_id": to_id,                # 🔥 CRITICAL FIELD
            "role": role,
            "from_date": data["from"],
            "to_date": data["to"],
            "reason": data.get("reason", ""),
            "type": data.get("type", ""),
            "part": data.get("part", ""),
            "comments": data.get("comments", ""),
            "days": days,
            "status": "Pending",
            "applied_on": datetime.utcnow().isoformat()
        })

        if not result:
            return jsonify({"status": "error", "message": "Insert failed"})

        return jsonify({"status": "success", "message": "Leave applied successfully"})

    except Exception as e:
        print("ERROR APPLY LEAVE:", str(e))
        return jsonify({"status": "error", "message": str(e)})
# ======================================================
# APPROVE LEAVE
# ======================================================
@app.route("/approve/<leave_id>", methods=["POST"])
def approve_leave(leave_id):

    if session.get("role") != "hr":
        return redirect("/login")

    reason = request.form.get("reason", "")

    # ✅ GET LEAVE
    leave = get_one("leaves", "id", leave_id)

    if not leave:
        return redirect("/hr")

    # ✅ GET HR DETAILS
    hr = get_one("employees", "emp_id", session.get("emp_id"))

    if not hr:
        return redirect("/hr")

    # 🚨 CHECK ADMIN ASSIGNED
    if not hr.get("admin_id"):
        return "Admin not assigned to HR"

    # 🔥 UPDATE → SEND TO ADMIN
    update_data(
        "leaves",
        "id",
        leave_id,
        {
            "status": "HR Approved",
            "to_id": hr.get("admin_id"),   # 🔥 IMPORTANT
            "hr_reason": reason
        }
    )

    # ✅ NOTIFICATION TO EMPLOYEE
    insert_data("notifications", {
        "emp_id": leave["emp_id"],
        "message": "✅ Your leave approved by HR",
        "read": False,
        "created_at": datetime.utcnow().isoformat()
    })

    return redirect("/hr")








# ======================================================
# CHANGE PASSWORD
# ======================================================
@app.route("/change_password",methods=["POST"])
def change_password():

    data=request.json
    emp_id=session.get("emp_id")

    user = get_one("users", "emp_id", emp_id)

    if user and user["password"] == data["old_password"]:

        update_data("users", "emp_id", emp_id,
                    {"password":data["new_password"]})
        return jsonify({"status":"success"})

    return jsonify({"status":"failed"})


# ======================================================
# ADMIN HR LEAVE REQUESTS
# ======================================================

@app.route("/admin_hr_leaves")
def admin_hr_leaves():

    if session.get("role") != "admin":
        return jsonify([])

    admin_id = session.get("emp_id")

    docs = supabase.table("leaves") \
        .select("*") \
        .eq("to_id", admin_id) \
        .eq("status", "Pending") \
        .execute().data

    return jsonify(docs)


@app.route("/admin_approve_leave", methods=["POST"])
def admin_approve_leave():

    if session.get("role") != "admin":
        return jsonify({"status": "unauthorized"})

    data = request.json
    leave_id = data["id"]

    update_data("leaves", "id", leave_id, {
        "status": "Approved",
        "to_id": None
    })

    return jsonify({"status": "approved"})


@app.route("/admin_reject_leave", methods=["POST"])
def admin_reject_leave():

    if session.get("role") != "admin":
        return jsonify({"status": "unauthorized"})

    data = request.json
    leave_id = data["id"]

    update_data("leaves", "id", leave_id, {
        "status": "Rejected",
        "to_id": None
    })

    return jsonify({"status": "rejected"})

# ======================================================
# DELETE PENDING LEAVE (EMPLOYEE)
# ======================================================
@app.route("/delete_leave", methods=["POST"])
def delete_leave():

    if not session.get("emp_id"):
        return jsonify({"status":"error"})

    data = request.json
    leave_id = data.get("id")
    emp_id = session.get("emp_id")

    # get leave
    leave = get_one("leaves", "id", leave_id)

    # safety checks
    if not leave:
        return jsonify({"status":"not_found"})

    # allow delete only own leave
    if leave["emp_id"] != emp_id:
        return jsonify({"status":"unauthorized"})

    # allow delete ONLY pending
    if leave["status"] != "Pending":
        return jsonify({"status":"not_allowed"})

    # delete
    delete_data("leaves", "id", leave_id)

    return jsonify({"status":"deleted"})




# ================= NEW JOINEES =================

@app.route("/new_joinees")
def new_joinees():

    if session.get("role") not in ["admin","hr","employee"]:
        return jsonify([])

    docs = supabase.table("employees") \
        .select("*") \
        .order("created_at", desc=True) \
        .execute().data

    return jsonify(docs)



@app.route("/profile_list")
def profile_list():

    docs = supabase.table("employees") \
        .select("name,dob,department") \
        .execute().data

    result = []

    for emp in docs:
        result.append({
            "name": emp.get("name"),
            "dob": emp.get("dob"),
            "department": emp.get("department")
        })

    return jsonify(result)
# ======================================================
# NOTIFICATIONS
# ======================================================
@app.route("/notifications_data")
def notifications_data():
    if not session.get("emp_id"):
        return jsonify({"notifications":[],"unread":0})
    emp_id=session.get("emp_id")

    docs = supabase.table("notifications") \
           .select("*") \
           .eq("emp_id", emp_id) \
           .order("created_at", desc=True) \
           .execute().data

    notifications=[]
    unread=0

    for n in docs:
        notifications.append(n)

        if not n.get("read"):
            unread+=1

    return jsonify({
        "notifications":notifications,
        "unread":unread
    })

@app.route("/mark_notification_read",methods=["POST"])
def mark_notification_read():

    data=request.json
    update_data("notifications", "id", data["id"], {"read": True})
    return jsonify({"status":"ok"})


# ======================================================
# ADD NOTIFICATION (SUPABASE VERSION)
# ======================================================
@app.route("/add_notification", methods=["POST"])
def add_notification():

    if not session.get("emp_id"):
        return jsonify({"status":"no_session"})

    data = request.json
    emp_id = session.get("emp_id")

    today = datetime.utcnow().strftime("%Y-%m-%d")
    ntype = data.get("type","general")

    existing = supabase.table("notifications") \
        .select("id") \
        .eq("emp_id", emp_id) \
        .eq("date", today) \
        .eq("type", ntype) \
        .execute().data

    if existing:
        return jsonify({"status":"exists"})

    insert_data("notifications", {
        "emp_id": emp_id,
        "message": data.get("message"),
        "type": ntype,
        "date": today,
        "read": False,
        "created_at": datetime.utcnow().isoformat()
    })

    return jsonify({"status":"ok"})


# ======================================================
# ADMIN DASHBOARD SUMMARY
# ======================================================
@app.route("/admin_summary")
def admin_summary():
    try:
        if session.get("role") != "admin":
            return jsonify({"error":"Unauthorized"})

        today = datetime.now().strftime("%Y-%m-%d")

        employees = get_all("employees")
        total_employees = len(employees)

        attendance_docs = supabase.table("attendance") \
            .select("*") \
            .eq("date", today) \
            .execute().data

        present = 0
        late = 0

        for a in attendance_docs:
            if a.get("checkin") and a["checkin"] > "10:05:00":
                late += 1
            else:
                present += 1

        absent = total_employees - len(attendance_docs)

        return jsonify({
            "total": total_employees,
            "present": present,
            "late": late,
            "absent": absent
        })

    except Exception as e:
        print("ADMIN SUMMARY ERROR:", e)
        return jsonify({
            "total":0,
            "present":0,
            "late":0,
            "absent":0
        })



@app.route("/register_face", methods=["POST"])
def register_face():

    try:
        if not session.get("emp_id"):
            return jsonify({"success": False, "msg": "Login required"})

        data = request.json
        emp_id = session.get("emp_id")

        image = data.get("image")

        if not image:
            return jsonify({"success": False, "msg": "No image received"})

        # ✅ REMOVE HEADER PART
        if "," not in image:
            return jsonify({"success": False, "msg": "Invalid image format"})
        image_data = image.split(",")[1]

        # ✅ DECODE BASE64
        img_bytes = base64.b64decode(image_data)

        file_name = f"{emp_id}.jpg"

        # ✅ UPLOAD TO SUPABASE (NO OPENCV)
        supabase.storage.from_("faces").upload(
            path=file_name,
            file=img_bytes,
            file_options={"content-type": "image/jpeg", "upsert": "true"}
        )

        # ✅ PUBLIC URL
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/faces/{file_name}"

        # ✅ SAVE IN DATABASE
        supabase.table("employees").update({
            "face_url": public_url
        }).eq("emp_id", emp_id).execute()

        return jsonify({"success": True})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"success": False, "msg": str(e)})
    

# ======================================================
# ADMIN YEARLY PERCENTAGE (REAL DATA)
# ======================================================
@app.route("/admin_yearly_percentage")
def admin_yearly_percentage():

    try:
        if session.get("role") != "admin":
            return jsonify({"error": "Unauthorized"})

        year = request.args.get("year")
        if not year:
            year = str(datetime.now().year)

        employees = get_all("employees")
        total_employees = len(employees)

        today = datetime.now().strftime("%Y-%m-%d")

        today_docs = supabase.table("attendance") \
            .select("*") \
            .eq("date", today) \
            .execute().data

        present_today = 0
        late_today = 0

        for a in today_docs:
            if a.get("checkin") and a["checkin"] > "10:05:00":
                late_today += 1
            else:
                present_today += 1

        absent_today = total_employees - len(today_docs)

        monthly_percentage = []

        for month in range(1, 13):

            start_date = f"{year}-{month:02d}-01"

            if month == 12:
                end_date = f"{year}-12-31"
            else:
                end_date = f"{year}-{month+1:02d}-01"

            month_docs = supabase.table("attendance") \
                .select("*") \
                .gte("date", start_date) \
                .lt("date", end_date) \
                .execute().data

            if not month_docs:
                monthly_percentage.append(0)
                continue

            total_present = len(month_docs)

            # Count working days in that month
            working_days = len(set([a["date"] for a in month_docs]))

            if working_days == 0 or total_employees == 0:
                monthly_percentage.append(0)
                continue

            max_possible = working_days * total_employees

            percent = round((total_present / max_possible) * 100, 2)

            monthly_percentage.append(percent)

        return jsonify({
            "total_employees": total_employees,
            "present_today": present_today,
            "late_today": late_today,
            "absent_today": absent_today,
            "monthly_percentage": monthly_percentage
        })

    except Exception as e:
        print("YEARLY PERCENTAGE ERROR:", e)
        return jsonify({
            "total_employees": 0,
            "present_today": 0,
            "late_today": 0,
            "absent_today": 0,
            "monthly_percentage": [0]*12
        })

# ======================================================
# ADMIN ATTENDANCE TABLE
# ======================================================
@app.route("/admin_attendance")
def admin_attendance():
    try:
        if session.get("role") != "admin":
            return jsonify([])

        date = request.args.get("date")
        department = request.args.get("department")

        # ===== FETCH ATTENDANCE SORTED (LATEST FIRST) =====
        query = supabase.table("attendance") \
            .select("*") \
            .order("date", desc=True)

        # Filter by specific date if provided
        if date:
            query = query.eq("date", date)

        attendance_docs = query.execute().data

        # ===== FETCH ALL EMPLOYEES ONCE =====
        employees = {
            e["emp_id"]: e
            for e in get_all("employees")
        }

        result = []

        for a in attendance_docs:

            emp = employees.get(a["emp_id"], {})

            # Filter by department if selected
            if department and emp.get("department") != department:
                continue

            # ===== STATUS LOGIC =====
            status = "Present"

            if a.get("checkin"):
                if a["checkin"] > "10:05:00":
                    status = "Late"
            else:
                status = "Absent"

            result.append({
                "emp_id": a.get("emp_id", ""),
                "name": emp.get("name", ""),
                "department": emp.get("department", ""),
                "date": a.get("date", ""),
                "checkin": a.get("checkin", ""),
                "status": status
            })

        # ===== EXTRA SAFETY SORT (IN CASE SUPABASE FAILS) =====
        result.sort(
            key=lambda x: x.get("date", ""),
            reverse=True
        )

        return jsonify(result)

    except Exception as e:
        print("ADMIN ATTENDANCE ERROR:", e)
        return jsonify([])

@app.route("/admin_department_stats")
def admin_department_stats():

    if session.get("role") != "admin":
        return jsonify({})

    employees = get_all("employees")

    dept_map = {}

    for emp in employees:
        dept = emp.get("department", "Unknown")
        dept_map.setdefault(dept, []).append(emp["emp_id"])

    today = datetime.now().strftime("%Y-%m-%d")

    docs = supabase.table("attendance") \
        .select("*") \
        .eq("date", today) \
        .execute().data

    departments = []
    percentages = []

    for dept, emp_ids in dept_map.items():

        departments.append(dept)

        present_count = sum(
            1 for d in docs if d["emp_id"] in emp_ids
        )

        total = len(emp_ids)

        percent = round((present_count / total) * 100, 2) if total else 0

        percentages.append(percent)

    return jsonify({
        "departments": departments,
        "percentages": percentages
    })

@app.route("/admin_year_trend")
def admin_year_trend():

    if session.get("role") != "admin":
        return jsonify({})

    current_year = datetime.now().year
    years = [current_year-2, current_year-1, current_year]

    employees = get_all("employees")
    total_employees = len(employees)

    percentages = []

    for year in years:

        docs = supabase.table("attendance") \
            .select("*") \
            .gte("date", f"{year}-01-01") \
            .lte("date", f"{year}-12-31") \
            .execute().data

        if not docs:
            percentages.append(0)
            continue

        total_present = len(docs)
        working_days = len(set(a["date"] for a in docs))

        max_possible = working_days * total_employees

        percent = round((total_present / max_possible) * 100, 2) if max_possible else 0

        percentages.append(percent)

    return jsonify({
        "years": years,
        "year_percentages": percentages
    })


@app.route("/admin_departments")
def admin_departments():

    if session.get("role") != "admin":
        return jsonify([])

    employees = get_all("employees")

    depts = sorted(
        list(set(
            e.get("department") for e in employees if e.get("department")
        ))
    )

    return jsonify(depts)

@app.route("/admin_add_employee", methods=["POST"])
def admin_add_employee():

    data = request.json

    supabase.table("employees").insert({
        "emp_id":data["emp_id"],
        "name":data["name"],
        "email":data["email"],
        "mobile":data["mobile"],
        "department":data["department"],
        "gender":data["gender"],
        "dob":data["dob"],
        "address":data["address"],
        "father":data["father"],
        "pan":data["pan"],
        "aadhaar":data["aadhaar"],
        "uan":data["uan"],
        "created_at":datetime.now().isoformat()
    }).execute()

    supabase.table("users").insert({
        "emp_id":data["emp_id"],
        "password":"1234",
        "role":"employee"
    }).execute()

    return jsonify({"success":True})

@app.route("/get_employee/<emp_id>")
def get_employee(emp_id):

    emp = supabase.table("employees") \
        .select("*") \
        .eq("emp_id", emp_id) \
        .execute().data

    if emp:
        return jsonify(emp[0])

    return jsonify({})

@app.route("/admin_update_profile", methods=["POST"])
def admin_update_profile():

    data = request.json

    supabase.table("employees") \
        .update({
            "name":data["name"],
            "email":data["email"],
            "mobile":data["mobile"],
            "department":data["department"],
            "gender":data["gender"],
            "dob":data["dob"],
            "address":data["address"],
            "father":data["father"],
            "pan":data["pan"],
            "aadhaar":data["aadhaar"],
            "uan":data["uan"]
        }) \
        .eq("emp_id", data["emp_id"]) \
        .execute()

    return jsonify({"success":True})
# ======================================================
# LOGOUT
# ======================================================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")




from math import radians, sin, cos, sqrt, atan2

OFFICE_LAT = 17.661489
OFFICE_LON = 74.043869
MAX_DISTANCE = 115000

def calculate_distance(lat1,lon1,lat2,lon2):

    R = 6371000

    dlat = radians(lat2-lat1)
    dlon = radians(lon2-lon1)

    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    c = 2 * atan2(sqrt(a),sqrt(1-a))

    return R*c


@app.route("/verify_location",methods=["POST"])
def verify_location():

    data=request.json

    try:
        lat = float(data.get("lat"))
        lon = float(data.get("lon"))
    except:
        return jsonify({"location": False, "device": False})
    
    device=data["device"]

    emp_id=session.get("emp_id")

    user=get_one("users","emp_id",emp_id)

    if not user:
        return jsonify({"location":False,"device":False})

    # device verify
    if not user.get("device_id"):
        update_data("users","emp_id",emp_id,{"device_id":device})

    elif user["device_id"]!=device:
        return jsonify({"location":False,"device":False})

    dist=calculate_distance(lat,lon,OFFICE_LAT,OFFICE_LON)

    print("Distance from office:", dist)

    if dist > MAX_DISTANCE:
        return jsonify({
            "location":False,
            "device":True,
            "distance":round(dist)
        })
        

    return jsonify({"location":True,"device":True})




@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():

    if not session.get("emp_id"):
        return jsonify({"success": False, "msg": "Login required"})

    data = request.json
    emp_id = session.get("emp_id")

    # ===== STEP 1: VERIFY LOCATION =====
    loc = requests.post("http://localhost:5000/verify_location", json={
        "lat": data["lat"],
        "lon": data["lon"],
        "device": data["device"]
    }).json()

    if not loc["location"] or not loc["device"]:
        return jsonify({"success": False, "msg": "Location/Device failed"})

    # ===== STEP 2: VERIFY FACE =====
    image = data["image"]

    image_data = image.split(",")[1]
    img_bytes = base64.b64decode(image_data)

    np_arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    emp = get_one("employees", "emp_id", emp_id)

    if not emp.get("face_url"):
        return jsonify({"success": False, "msg": "Face not registered"})

    response = requests.get(emp["face_url"])
    stored = np.frombuffer(response.content, np.uint8)
    stored = cv2.imdecode(stored, cv2.IMREAD_COLOR)

    result = DeepFace.verify(img, stored, enforce_detection=False)

    if not result["verified"]:
        return jsonify({"success": False, "msg": "Face mismatch"})

    # ===== STEP 3: ATTENDANCE =====
    today = datetime.now().strftime("%Y-%m-%d")
    now_time = datetime.now().strftime("%H:%M:%S")

    record = supabase.table("attendance") \
        .select("*") \
        .eq("emp_id", emp_id) \
        .eq("date", today) \
        .execute().data

    if not record:
        insert_data("attendance", {
            "emp_id": emp_id,
            "date": today,
            "checkin": now_time,
            "status": "Present"
        })
        return jsonify({"success": True, "type": "checkin"})

    else:
        if not record[0].get("checkout"):
            update_data("attendance", "id", record[0]["id"], {
                "checkout": now_time
            })
            return jsonify({"success": True, "type": "checkout"})

        return jsonify({"success": True, "type": "done"})
    
    
# ======================================================
# RUN
# ======================================================
if __name__=="__main__":
    app.run(debug=True, use_reloader=False)

