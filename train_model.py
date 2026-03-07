import cv2
import numpy as np
import os

recognizer = cv2.face.LBPHFaceRecognizer_create()

faces, labels = [], []

for label in os.listdir("dataset"):
    folder = os.path.join("dataset", label)
    for img in os.listdir(folder):
        path = os.path.join(folder, img)
        gray = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if gray is None:
            continue
        faces.append(gray)
        labels.append(int(label))

recognizer.train(faces, np.array(labels))
os.makedirs("trainer", exist_ok=True)
recognizer.save("trainer/face_trainer.yml")

print("✅ Training completed successfully")
