import firebase_admin
from firebase_admin import credentials, firestore
from supabase import create_client
from datetime import datetime
import time

# ================= FIREBASE =================
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

# ================= SUPABASE =================
SUPABASE_URL = "https://orrohkftvhqogzvekvrt.supabase.co"
SUPABASE_KEY = "sb_publishable_WbtaMGk4jOcG-yA83JBxiw_8wz-iCnA"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================= CLEAN DATA =================
def clean_data(data):
    for k, v in data.items():
        if isinstance(v, datetime):
            data[k] = v.isoformat()
    return data


# ================= MIGRATE USERS =================
print("🚀 Migrating USERS...")

docs = db.collection("users").stream()

count = 0

for doc in docs:

    data = doc.to_dict()

    # keep firestore document id
    data["emp_id"] = doc.id

    data = clean_data(data)

    try:
        supabase.table("users").insert(data).execute()
        count += 1
        print(f"✅ Inserted user {count}")

        # prevent quota error
        time.sleep(0.5)

    except Exception as e:
        print("❌ Error:", e)

print(f"\n🎉 USERS MIGRATION COMPLETE: {count} records")