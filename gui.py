import tkinter as tk
from tkinter import messagebox
import pandas as pd
import os

ATTENDANCE_FILE = "Attendance/attendance.csv"
USERS_FILE = "users.csv"

# =====================
# LOGIN WINDOW
# =====================
def login():
    username = entry_user.get()
    password = entry_pass.get()

    if not os.path.exists(USERS_FILE):
        messagebox.showerror("Error", "users.csv not found")
        return

    users = pd.read_csv(USERS_FILE)
    user = users[(users.Username==username) & (users.Password==password)]

    if user.empty:
        messagebox.showerror("Login Failed", "Invalid username or password")
        return

    role = user.iloc[0]["Role"]
    empid = user.iloc[0]["EmpID"]

    root.destroy()

    if role == "Admin":
        admin_dashboard()
    else:
        employee_dashboard(empid)

# =====================
# ADMIN DASHBOARD
# =====================
def admin_dashboard():
    win = tk.Tk()
    win.title("Admin Dashboard")

    tk.Label(win, text="All Attendance Records", font=("Arial",14)).pack()

    if os.path.exists(ATTENDANCE_FILE):
        df = pd.read_csv(ATTENDANCE_FILE)
        text = tk.Text(win, width=120, height=30)
        text.pack()
        text.insert(tk.END, df.to_string(index=False))
    else:
        tk.Label(win, text="No attendance data").pack()

    win.mainloop()

# =====================
# EMPLOYEE DASHBOARD
# =====================
def employee_dashboard(empid):
    win = tk.Tk()
    win.title("Employee Dashboard")

    tk.Label(win, text=f"Attendance for {empid}", font=("Arial",14)).pack()

    if os.path.exists(ATTENDANCE_FILE):
        df = pd.read_csv(ATTENDANCE_FILE)
        df = df[df.EmpID == empid]

        text = tk.Text(win, width=120, height=30)
        text.pack()
        text.insert(tk.END, df.to_string(index=False))
    else:
        tk.Label(win, text="No attendance data").pack()

    win.mainloop()

# =====================
# MAIN LOGIN UI
# =====================
root = tk.Tk()
root.title("Face Attendance Login")

tk.Label(root, text="Username").grid(row=0, column=0, padx=10, pady=10)
entry_user = tk.Entry(root)
entry_user.grid(row=0, column=1)

tk.Label(root, text="Password").grid(row=1, column=0, padx=10, pady=10)
entry_pass = tk.Entry(root, show="*")
entry_pass.grid(row=1, column=1)

tk.Button(root, text="Login", command=login, width=15).grid(row=2, column=1, pady=15)

root.mainloop()
