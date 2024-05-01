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
from cryptography.fernet import Fernet


logger = logging.getLogger()

class WebcamReader:
	
	def __init__(self, *args, **kwargs):
		self.cap = cv.VideoCapture(0)
		self.frame_skip = 5
		self.access_denied_images_path = "denied_access_images"
		self.user_storage = UserStorage()
		if not self.cap.isOpened():
			logging.warning("Failed to open camera. Is an active webcam present?")
		if not os.path.exists(self.access_denied_images_path):
			os.makedirs(self.access_denied_images_path)

	async def get_known_encodings(self):
		user_list = await self.user_storage.list_users()
		print(user_list)
		known_face_encodings = []
		known_face_names = []

		for username, _, _ in user_list:
			face_encoding = await self.user_storage.get_user_encoding(username)
			if face_encoding is not None:
				known_face_names.append(username)
				known_face_encodings.append(face_encoding)
			else:
				logger.warning(f"Failed to retrieve or decode face encoding for {username}")

		return known_face_names, known_face_encodings


	async def read_webcam(self, *args, **kwargs):
		known_face_names, known_face_encodings = await self.get_known_encodings()

		while True:
			ret, frame = self.cap.read()
			if not ret:
				continue

			# Resize the frame to reduce resolution and speed up face processing
			small_frame = cv.resize(frame, (0, 0), fx=0.5, fy=0.5)

			# Convert the image from BGR color (which OpenCV uses)
			# to RGB color (which face_recognition uses)
			rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])

			# Find all the faces and face encodings in the resized frame
			face_locations = face_recognition.face_locations(rgb_small_frame)
			face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)


			# EDIT: # Set a new threshold for face comparison
			threshold = 0.5  # Lower value makes the comparison stricter

			# Loop through each face in this frame of video
			for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
				# Scale face locations back up to the original frame size
				top *= 2; right *= 2; bottom *= 2; left *= 2

				# Compare the face encoding to known face encodings
				matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
				name = "Unknown"
				# EDIT: add access denied message 
				access_message = "Access Denied"

				# If a match was found in known_face_encodings, just use the first one.
				if any(matches):
					first_match_index = matches.index(True)
					name = known_face_names[first_match_index]
					access_message = "Access Granted"

				# Draw a box around the face
				cv.rectangle(frame, (left, top), (right, bottom), (0, 255, 0) if access_message == "Access Granted" else (255, 0, 0), 2)

				# Draw a label with a name and access message below the face
				cv.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0) if access_message == "Access Granted" else (255, 0, 0), cv.FILLED)
				font = cv.FONT_HERSHEY_DUPLEX
				cv.putText(frame, f"{name}: {access_message}", (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)

			# Display the resulting frame
			cv.imshow('Video', frame)

			# Break the loop if 'q' is pressed
			if cv.waitKey(1) & 0xFF == ord('q'):
				break

		# Release the webcam and destroy all OpenCV windows
		self.cap.release()
		cv.destroyAllWindows()