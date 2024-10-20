# app.py
from flask import Flask, request, jsonify, render_template
from flask_mail import Mail, Message
import face_recognition
import numpy as np
from twilio.rest import Client
from models import db, Student

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Replace with your mail server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '2003010057@ipec.org.in'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'ASMIT10057'  # Replace with your email password
db.init_app(app)
mail = Mail(app)

# Twilio configuration
# TWILIO_ACCOUNT_SID = 'your_twilio_account_sid'
# TWILIO_AUTH_TOKEN = 'your_twilio_auth_token'
# TWILIO_PHONE_NUMBER = 'your_twilio_phone_number'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_student', methods=['POST'])
def add_student():
    data = request.form
    file = request.files['file']
    image = face_recognition.load_image_file(file)
    face_encoding = face_recognition.face_encodings(image)[0]

    student = Student(
        roll_no=data['roll_no'],
        name=data['name'],
        email=data['email'],
        phone=data['phone'],
        face_encoding=face_encoding.tobytes(),
        image=file.read()
    )

    db.session.add(student)
    db.session.commit()
    return jsonify({"message": "Student added successfully!"})

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    image = face_recognition.load_image_file(file)
    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)

    recognized_students = []
    for encoding in face_encodings:
        matches = []
        for student in Student.query.all():
            known_encoding = np.frombuffer(student.face_encoding)
            match = face_recognition.compare_faces([known_encoding], encoding)
            if match[0]:
                matches.append(student)
                break

        if matches:
            recognized_students.append(matches[0])

    attendance = {student.name: 'Present' for student in recognized_students}

    for student in recognized_students:
        send_notification(student)

    return jsonify(attendance)

def send_notification(student):
    send_email(student.email, student.name)
    # send_sms(student.phone, student.name)

def send_email(email, name):
    msg = Message('Attendance Notification', sender='your_email@example.com', recipients=[email])
    msg.body = f"Dear {name},\n\nYou have been marked present today.\n\nBest regards,\nAttendance System"
    mail.send(msg)

# def send_sms(phone, name):
#     client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
#     message = client.messages.create(
#         body=f"Dear {name}, You have been marked present today.",
#         from_=TWILIO_PHONE_NUMBER,
#         to=phone
#     )

if __name__ == '__main__':
    app.run(debug=True)
