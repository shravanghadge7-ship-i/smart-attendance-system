import tkinter as tk
from tkinter import ttk
import pandas as pd
import calendar
from datetime import datetime
import os

# =============================
# FILE PATHS
# =============================
ATTENDANCE_FILE = "Attendance/attendance.csv"
EMP_FILE = "employees.csv"

# =============================
# SAFETY CHECK
# =============================
if not os.path.exists(ATTENDANCE_FILE):
    raise FileNotFoundError("attendance.csv not found")

if not os.path.exists(EMP_FILE):
    raise FileNotFoundError("employees.csv not found")

employees = pd.read_csv(EMP_FILE)

# =============================
# MAIN WINDOW
# =============================
root = tk.Tk()
root.title("Admin Monthly Attendance Dashboard")
root.geometry("950x600")
root.configure(bg="white")

# =============================
# TITLE
# =============================
tk.Label(
    root,
    text="MONTHLY ATTENDANCE CALENDAR",
    font=("Arial", 18, "bold"),
    bg="white"
).pack(pady=15)

# =============================
# TOP CONTROLS
# =============================
top = tk.Frame(root, bg="white")
top.pack(pady=10)

tk.Label(top, text="Employee:", bg="white").grid(row=0, column=0, padx=5)

emp_var = tk.StringVar()
emp_combo = ttk.Combobox(top, textvariable=emp_var, width=30, state="readonly")
emp_combo["values"] = [f"{row.EmpID} - {row.Name}" for _, row in employees.iterrows()]
emp_combo.grid(row=0, column=1, padx=5)

tk.Label(top, text="Month:", bg="white").grid(row=0, column=2, padx=5)

month_var = tk.StringVar()
month_combo = ttk.Combobox(
    top,
    textvariable=month_var,
    state="readonly",
    width=15,
    values=list(calendar.month_name)[1:]
)
month_combo.grid(row=0, column=3, padx=5)

tk.Label(top, text="Year:", bg="white").grid(row=0, column=4, padx=5)

year_var = tk.StringVar(value=str(datetime.now().year))
year_combo = ttk.Combobox(
    top,
    textvariable=year_var,
    values=[str(y) for y in range(2023, 2031)],
    width=10,
    state="readonly"
)
year_combo.grid(row=0, column=5, padx=5)

# =============================
# CALENDAR FRAME
# =============================
calendar_frame = tk.Frame(root, bg="white")
calendar_frame.pack(pady=20)

# =============================
# FUNCTIONS
# =============================
def clear_calendar():
    for widget in calendar_frame.winfo_children():
        widget.destroy()

def show_calendar():
    clear_calendar()

    if not emp_var.get() or not month_var.get():
        return

    attendance = pd.read_csv(ATTENDANCE_FILE)

    emp_id = emp_var.get().split(" - ")[0]
    month = list(calendar.month_name).index(month_var.get())
    year = int(year_var.get())

    emp_att = attendance[
        (attendance["EmpID"] == emp_id) &
        (attendance["Date"].str.startswith(f"{year}-{month:02d}"))
    ]

    # Week headers
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i, d in enumerate(days):
        tk.Label(
            calendar_frame,
            text=d,
            font=("Arial", 10, "bold"),
            bg="white",
            width=12
        ).grid(row=0, column=i)

    cal = calendar.monthcalendar(year, month)

    for r, week in enumerate(cal, start=1):
        for c, day in enumerate(week):
            if day == 0:
                tk.Label(
                    calendar_frame,
                    text="",
                    bg="white",
                    width=12,
                    height=4
                ).grid(row=r, column=c)
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                record = emp_att[emp_att["Date"] == date_str]

                if not record.empty:
                    status = record.iloc[0]["Status"]

                    if status == "On Time":
                        bg = "#b6fcb6"      # Green
                        text = f"{day}\nOn Time"
                    elif status == "Late":
                        bg = "#fff3b0"      # Yellow
                        text = f"{day}\nLate"
                    elif status == "Completed":
                        bg = "#b3d9ff"      # Blue
                        text = f"{day}\nCompleted"
                    else:
                        bg = "#dddddd"
                        text = f"{day}\nPresent"
                else:
                    bg = "#ffb3b3"          # Red
                    text = f"{day}\nAbsent"

                tk.Label(
                    calendar_frame,
                    text=text,
                    bg=bg,
                    width=12,
                    height=4,
                    relief="solid"
                ).grid(row=r, column=c, padx=2, pady=2)

# =============================
# BUTTON
# =============================
tk.Button(
    root,
    text="View Attendance",
    font=("Arial", 11, "bold"),
    command=show_calendar
).pack(pady=10)

# =============================
# START
# =============================
root.mainloop()
