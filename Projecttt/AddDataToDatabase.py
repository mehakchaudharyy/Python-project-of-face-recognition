import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': " "
})

ref = db.reference('Students')

data = {
    "1345":
        {
            "Name": "Mehak Chaudhary",
            "Course": "BE-CSE",
            "Starting_Year": 2024,
            "total_attendance": 1,
            "year": 1,
            "last_attendance_time": "23-04-2025 00:54:34"
        },
    "1378":
        {
            "Name": "Nikita Arora",
            "Course": "BE-CSE",
            "Starting_Year": 2024,
            "total_attendance": 1,
            "year": 1,
            "last_attendance_time": "23-04-2025 00:54:34"
        },
    }

for key, value in data.items():
    ref.child(key).set(value)