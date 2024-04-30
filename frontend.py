import logging
import cv2 as cv
import numpy as np
import face_recognition
from storage import UserStorage
from PIL import UnidentifiedImageError
import os
import hashlib
import unittest
from aes import AES, encrypt, decrypt


logger = logging.getLogger()

class WebcamReader:
    
    def _init_(self, *args, **kwargs):
        self.cap = cv.VideoCapture(0)
        self.frame_skip = 5
        self.access_denied_images_path = "denied_access_images"
        self.encryption_key = os.urandom(32)  # AES-256 key
        self.iv = os.urandom(16)  # Initialization vector
        self.aes_instance = AES(self.encryption_key)  # Create an instance of the AES class
        if not self.cap.isOpened():
            logging.warning("Failed to open camera. Is an active webcam present?")
        if not os.path.exists(self.access_denied_images_path):
            os.makedirs(self.access_denied_images_path)

    async def get_known_encodings(self, *args, **kwargs):
        user_storage = UserStorage()
        user_list = await user_storage.list_users()
        known_face_encodings = []
        known_face_names = []

        for user_info in user_list:
            try:
                user_image = face_recognition.load_image_file(user_info[1])
                user_image_encoding = face_recognition.face_encodings(user_image)[0]
                known_face_names.append(user_info[0])
                # Encrypt the face encoding before storing it
                encrypted_encoding = self.aes_instance.encrypt(user_image_encoding.tobytes(), self.iv)
                # Decrypt the face encoding and reshape it back to (128,)
                decrypted_encoding = self.aes_instance.decrypt(encrypted_encoding, self.iv)
                face_encoding = np.frombuffer(decrypted_encoding, dtype=np.float64).reshape(-1)
                known_face_encodings.append(face_encoding)
            except UnidentifiedImageError:
                logging.warning(f"Failed to determine face_encoding for: {user_info[1]}")
                continue

        return known_face_names, known_face_encodings


    async def read_webcam(self, *args, **kwargs):
        known_face_names, known_face_encodings = await self.get_known_encodings()
        frame_count = 0
        recognition_threshold = 0.6  # Set the threshold for face recognition

        while True:
            ret, frame = self.cap.read()
            frame_count += 1

            # Skip frames to reduce lag
            if frame_count % self.frame_skip != 0:
                continue

            rgb_frame = frame[:, :, ::-1]
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                access_granted = face_distances[best_match_index] < recognition_threshold

                name = known_face_names[best_match_index] if access_granted else "Unknown"

                # Draw a box around the face and show pop-up message
                box_color = (0, 255, 0) if access_granted else (0, 0, 255)
                cv.rectangle(frame, (left, top), (right, bottom), box_color, 2)
                font = cv.FONT_HERSHEY_DUPLEX
                cv.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

                # If access is denied, save the image and show a pop-up
                if not access_granted:
                    timestamp = hashlib.sha256(str(top + right + bottom + left).encode()).hexdigest()
                    denied_image_path = os.path.join(self.access_denied_images_path, f"{timestamp}.png")
                    cv.imwrite(denied_image_path, frame[top:bottom, left:right])
                    cv.imshow('Access Denied', frame[top:bottom, left:right])

            cv.imshow('Video', frame)

            if cv.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv.destroyAllWindows()