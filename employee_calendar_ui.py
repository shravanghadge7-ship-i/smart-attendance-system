import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase Init
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def submit_leave():

    emp_id = emp_entry.get()
    from_date = from_entry.get()
    to_date = to_entry.get()
    reason = reason_entry.get()

    if emp_id=="" or from_date=="" or to_date=="":
        messagebox.showerror("Error","Fill all fields")
        return

    db.collection("leaves").add({
        "emp_id": emp_id,
        "from_date": from_date,
        "to_date": to_date,
        "reason": reason,
        "status": "pending",
        "timestamp": firestore.SERVER_TIMESTAMP
    })

    messagebox.showinfo("Success","Leave Applied Successfully")

    emp_entry.delete(0,"end")
    from_entry.delete(0,"end")
    to_entry.delete(0,"end")
    reason_entry.delete(0,"end")

root = tk.Tk()
root.title("Employee Leave Application")
root.geometry("350x300")

tk.Label(root,text="Employee ID").pack()
emp_entry = tk.Entry(root)
emp_entry.pack()

tk.Label(root,text="From Date (YYYY-MM-DD)").pack()
from_entry = tk.Entry(root)
from_entry.pack()

tk.Label(root,text="To Date (YYYY-MM-DD)").pack()
to_entry = tk.Entry(root)
to_entry.pack()

tk.Label(root,text="Reason").pack()
reason_entry = tk.Entry(root)
reason_entry.pack()

tk.Button(root,text="Apply Leave",command=submit_leave,bg="green",fg="white").pack(pady=10)

root.mainloop()
