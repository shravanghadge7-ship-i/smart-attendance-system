from flask import Flask, render_template
import os

app = Flask(__name__)

@app.route("/")
def home():
    print("HOME LOADED")
    return render_template("index.html")

@app.route("/register")
def register():
    print("REGISTER CLICKED")
    os.system("python face_dataset.py")
    os.system("python train_model.py")
    return "Register Done"

@app.route("/checkin")
def checkin():
    print("CHECK-IN CLICKED")
    os.system("python attendance.py")
    return "Check-in Done"

@app.route("/checkout")
def checkout():
    print("CHECK-OUT CLICKED")
    os.system("python attendance.py")
    return "Check-out Done"

if __name__ == "__main__":
    app.run(debug=True)