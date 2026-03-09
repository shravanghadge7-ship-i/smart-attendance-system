SMART ATTENDANCE SYSTEM USING FACE RECOGNITION

Steps to Run:

1. Capture face dataset
   python face_dataset.py

2. Train model
   python train_model.py

3. Run attendance system
   python attendance.py

Press ESC to exit camera.












# ======================================================
# NOTIFICATIONS
# ======================================================
@app.route("/notifications_data")
def notifications_data():
    if not session.get("emp_id"):
        return jsonify({"notifications":[],"unread":0})
    emp_id=session.get("emp_id")

    docs=db.collection("notifications") \
           .where("emp_id","==",emp_id) \
           .order_by("created_at",
                 direction=firestore.Query.DESCENDING) \
           .stream()

    notifications=[]
    unread=0

    for d in docs:
        n=d.to_dict()
        n["id"]=d.id
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
    db.collection("notifications").document(data["id"]).update({"read":True})
    return jsonify({"status":"ok"})











# ======================================================
# ENSURE PROFILE EXISTS
# ======================================================
def ensure_employee_profile(emp_id):
    if not emp_id:
        return
    ref=db.collection("employees").document(emp_id)
    if not ref.get().exists:
        ref.set(default_profile())

# ======================================================
# HOME
# ======================================================
@app.route("/")
def home():
    return redirect("/login")

# ======================================================
# LOGIN
# ======================================================
@app.route("/login",methods=["GET","POST"])
def login():

    if request.method=="POST":

        emp_id=request.form.get("emp_id")
        password=request.form.get("password")

        user=db.collection("users").document(emp_id).get()

        if user.exists and user.to_dict().get("password")==password:

            ensure_employee_profile(emp_id)
            emp=db.collection("employees").document(emp_id).get().to_dict() or {}

            session["emp_id"]=emp_id
            session["role"]=user.to_dict().get("role")
            session["name"]=emp.get("name","Employee")
            session["photo"]=user.to_dict().get("photo","https://via.placeholder.com/100")

            return redirect("/"+session["role"])

    return render_template("login.html")

# ======================================================
# PROFILE APIs
# ======================================================
@app.route("/profile")
def profile():

    emp_id=session.get("emp_id")
    if not emp_id:
        return jsonify({})

    ensure_employee_profile(emp_id)
    data=db.collection("employees").document(emp_id).get().to_dict() or {}

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
    if not emp_id:
        return jsonify({})

    ensure_employee_profile(emp_id)
    data=db.collection("employees").document(emp_id).get().to_dict() or {}

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
        "photo":session.get("photo")
    })

# ======================================================
# ADMIN PANEL
# ======================================================
@app.route("/admin")
def admin():

    if session.get("role")!="admin":
        return redirect("/login")

    users=[{"id":u.id,"role":u.to_dict().get("role")}
           for u in db.collection("users").stream()]

    employees=[]
    for e in db.collection("employees").stream():
        d=e.to_dict() or {}
        d["id"]=e.id
        employees.append(d)

    return render_template("admin.html",users=users,employees=employees)

@app.route("/add_user",methods=["POST"])
def add_user():

    emp_id=request.form.get("id")

    db.collection("users").document(emp_id).set({
        "password":request.form.get("password"),
        "role":request.form.get("role"),
        "photo":"https://via.placeholder.com/100"
    })

    ensure_employee_profile(emp_id)
    return redirect("/admin")

@app.route("/update_employee",methods=["POST"])
def update_employee():

    if session.get("role")!="admin":
        return redirect("/login")

    emp_id=request.form.get("emp_id")
    email=request.form.get("email","")

    if email and not valid_email(email):
        return "Invalid Email Format"

    update_data={
        "name":request.form.get("name",""),
        "email":email,
        "mobile":request.form.get("mobile",""),
        "department":request.form.get("department",""),
        "gender":request.form.get("gender",""),
        "dob":request.form.get("dob",""),
        "address":request.form.get("address",""),
        "father":request.form.get("father",""),
        "updated_at":datetime.now()
    }

    db.collection("employees").document(emp_id).set(update_data,merge=True)
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
# HR DASHBOARD
# ======================================================
@app.route("/hr")
def hr():

    if session.get("role") != "hr":
        return redirect("/login")

    emp_filter = request.args.get("emp_id")

    leaves=[]
    emp_set=set()

    docs = db.collection("leaves") \
        .order_by("applied_on",
                  direction=firestore.Query.DESCENDING) \
        .stream()

    for d in docs:

        l=d.to_dict() or {}
        l["id"]=d.id

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

    pending_docs = db.collection("leaves") \
        .where("status","==","Pending") \
        .stream()

    count = sum(1 for _ in pending_docs)

    return jsonify({"pending":count})

# ======================================================
# ATTENDANCE API
# ======================================================
@app.route("/attendance")
def attendance_data():
    if not session.get("emp_id"):
        return jsonify([])
    emp_id=session.get("emp_id")
    docs=db.collection("attendance").where("emp_id","==",emp_id).stream()

    data=[]
    for d in docs:
        data.append(d.to_dict() or {})

    return jsonify(data)

# ======================================================
# LEAVES API
# ======================================================
@app.route("/leaves")
def leaves_data():
    if not session.get("emp_id"):
        return jsonify([])
    emp_id=session.get("emp_id")
    docs=db.collection("leaves").where("emp_id","==",emp_id).stream()

    data=[]
    for d in docs:
        l=d.to_dict() or {}
        l["id"]=d.id
        data.append(l)

    return jsonify(data)

# ======================================================
# APPLY LEAVE
# ======================================================
@app.route("/apply_leave",methods=["POST"])
def apply_leave():
    if not session.get("emp_id"):
        return jsonify({"status":"error"})
    data=request.json
    emp_id=session.get("emp_id")

    db.collection("leaves").add({
        "emp_id":emp_id,
        "from_date":data.get("from"),
        "to_date":data.get("to"),
        "reason":data.get("reason"),
        "type":data.get("type",""),
        "part":data.get("part",""),
        "comments":data.get("comments",""),
        "days":data.get("days",""),
        "status":"Pending",
        "applied_on":datetime.now()
    })

    return jsonify({"status":"ok"})

# ======================================================
# REJECT LEAVE
# ======================================================
@app.route("/reject/<leave_id>",methods=["POST"])
def reject_leave(leave_id):

    if session.get("role")!="hr":
        return redirect("/login")

    reason=request.form.get("reason","")

    ref=db.collection("leaves").document(leave_id)
    doc=ref.get()

    if not doc.exists:
        return redirect("/hr")

    data=doc.to_dict() or {}

    ref.update({"status":"Rejected","hr_reason":reason})

    if data.get("emp_id"):
        db.collection("notifications").add({
            "emp_id":data.get("emp_id"),
            "message":"❌ Your leave has been rejected",
            "read":False,
            "created_at":datetime.now()
        })

    return redirect("/hr")

# ======================================================
# APPROVE LEAVE
# ======================================================
@app.route("/approve/<leave_id>",methods=["POST"])
def approve_leave(leave_id):

    if session.get("role")!="hr":
        return redirect("/login")

    ref=db.collection("leaves").document(leave_id)
    doc=ref.get()

    if not doc.exists:
        return redirect("/hr")

    data=doc.to_dict() or {}

    ref.update({"status":"Approved"})

    if data.get("emp_id"):
        db.collection("notifications").add({
            "emp_id":data.get("emp_id"),
            "message":"✅ Your leave has been approved",
            "read":False,
            "created_at":datetime.now()
        })

    return redirect("/hr")

# ======================================================
# CHANGE PASSWORD
# ======================================================
@app.route("/change_password",methods=["POST"])
def change_password():

    data=request.json
    emp_id=session.get("emp_id")

    user_ref=db.collection("users").document(emp_id)
    user=user_ref.get()

    if user.exists and user.to_dict().get("password")==data.get("old_password"):

        user_ref.update({"password":data.get("new_password")})
        return jsonify({"status":"success"})

    return jsonify({"status":"failed"})













python add_sample_data.py
21-5-2025 emp2
14-2-2025 emp1 15-1-26


real time create 5 chart for continues upgrade as per year or month many chart are present in  dashboard real time so what can do you