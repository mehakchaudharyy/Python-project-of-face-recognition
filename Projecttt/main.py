import pickle
import cv2
import os
import numpy as np
import face_recognition
import cvzone
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from datetime import datetime

# Firebase setup
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': " ",
    'storageBucket': " "
})
bucket = storage.bucket()

# Camera setup
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

# Load background and mode images
imgBackground = cv2.imread('Resources/bg.png')
folderModePath = 'Resources/Modes'
modePathList = os.listdir(folderModePath)
imgModeList = [cv2.imread(os.path.join(folderModePath, path)) for path in modePathList]

# Load encoding file
with open('EncodeFile.p', 'rb') as file:
    encodeListKnownWithIds = pickle.load(file)
encodeListKnown, studentIds = encodeListKnownWithIds

modeType = 0
counter = 0
id = -1
imgStudent = []

while True:
    success, img = cap.read()
    if not success or img is None:
        print("Failed to capture image from webcam")
        continue

    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

    imgBackground[162:162 + 480, 55:55 + 640] = img
    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

    for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
        matchIndex = np.argmin(faceDis)

        if matches[matchIndex]:
            y1, x2, y2, x1 = faceLoc
            y1, x2, y2, x1 = [v * 4 for v in (y1, x2, y2, x1)]
            bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
            imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
            id = studentIds[matchIndex]

            if counter == 0:
                counter = 1
                modeType = 1

    if counter != 0:
        if counter == 1:
            # Get student data
            studentInfo = db.reference(f'Students/{id}').get()
            print(studentInfo)

            # Get student image from Firebase storage
            blob = bucket.get_blob(f'Images/{id}.png')
            array = np.frombuffer(blob.download_as_string(), np.uint8)
            imgStudent = cv2.imdecode(array, cv2.IMREAD_COLOR)

            # Resize to fit placeholder
            imgStudent = cv2.resize(imgStudent, (216, 216))

            # Attendance logic
            datetimeObject = datetime.strptime(studentInfo['last_attendance_time'], "%d-%m-%Y %H:%M:%S")
            secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
            print(secondsElapsed)

            if secondsElapsed > 30:
                ref = db.reference(f'Students/{id}')
                studentInfo['total_attendance'] += 1
                ref.child('total_attendance').set(studentInfo['total_attendance'])
                ref.child('last_attendance_time').set(datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
            else:
                modeType = 3
                counter = 0
                imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

        if modeType != 3:
            if 10 < counter < 20:
                modeType = 2
            imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

            if counter <= 10:
                cv2.putText(imgBackground, str(studentInfo['total_attendance']), (861, 125),
                            cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                cv2.putText(imgBackground, str(studentInfo['Course']), (1006, 550),
                            cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(imgBackground, str(id), (1006, 493),
                            cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(imgBackground, str(studentInfo['year']), (1025, 625),
                            cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                cv2.putText(imgBackground, str(studentInfo['Starting_Year']), (1125, 625),
                            cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)

                (w, h), _ = cv2.getTextSize(studentInfo['Name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                offset = (414 - w) // 2
                cv2.putText(imgBackground, str(studentInfo['Name']), (808 + offset, 445),
                            cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)

                imgBackground[175:175 + 216, 909:909 + 216] = imgStudent

            counter += 1
            if counter >= 20:
                counter = 0
                modeType = 0
                studentInfo = []
                imgStudent = []
                imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
    else:
        modeType = 0
        counter = 0

    cv2.imshow("Face Attendance", imgBackground)
    cv2.waitKey(1)
