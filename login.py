import pandas as pd

print("\n===== LOGIN SYSTEM =====\n")

# Force all columns as string
df = pd.read_csv("users.csv", dtype=str)

username = input("Enter username: ").strip()
password = input("Enter password: ").strip()

# Filter user
user = df[
    (df["Username"].str.strip() == username) &
    (df["Password"].str.strip() == password)
]

if user.empty:
    print("❌ Invalid username or password")
    exit()

role = str(user.iloc[0]["Role"]).strip()
emp_id = str(user.iloc[0]["EmpID"]).strip()

print(f"\n✅ Login successful")
print(f"Role: {role}")
print(f"EmpID: {emp_id}\n")

if role.lower() == "admin":
    import admin_dashboard
elif role.lower() == "employee":
    import employee_dashboard
