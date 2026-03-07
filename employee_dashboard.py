import tkinter as tk
import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def fetch_data():

    emp_id = emp_entry.get()

    result.delete("1.0","end")

    leaves = db.collection("leaves").where("emp_id","==",emp_id).stream()

    for doc in leaves:
        d = doc.to_dict()
        result.insert("end",f"From: {d['from_date']}  To: {d['to_date']}  Status: {d['status']}\n")

root = tk.Tk()
root.title("Employee Dashboard")
root.geometry("400x300")

tk.Label(root,text="Employee ID").pack()
emp_entry = tk.Entry(root)
emp_entry.pack()

tk.Button(root,text="Check Leave Status",command=fetch_data).pack()

result = tk.Text(root,height=10)
result.pack()

root.mainloop()
