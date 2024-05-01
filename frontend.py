import logging
from storage import UserStorage
import cv2 as cv
import numpy as np
import face_recognition
import os
import datetime
from time import time, sleep


logger = logging.getLogger()

class WebcamReader:

	def __init__(self, threshold=0.6, reset_interval=300, denial_interval=15):
		self.cap = cv.VideoCapture(0)
		self.threshold = threshold
		self.reset_interval = reset_interval  # Reset every 5 minutes
		self.denial_interval = denial_interval # Only captures one denied image within this interval
		self.access_denied_images_path = "denied_access_images"
		self.denial_record = {}
		self.last_reset_time = time()
		self.user_storage = UserStorage()
		self.frame_skip = 2

		if not self.cap.isOpened():
			print("Failed to open camera.")
		if not os.path.exists(self.access_denied_images_path):
			os.makedirs(self.access_denied_images_path)


	async def get_known_encodings(self):
		"""
		Retrieves and returns known face encodings and their corresponding user names from the storage.
		This method queries the user storage for all registered users and fetches their face encodings.
		"""
		user_list = await self.user_storage.list_users()
		known_face_encodings = []
		known_face_names = []

		for username, _, _ in user_list:
			face_encoding = await self.user_storage.get_user_encoding(username)
			if face_encoding is not None:
				known_face_names.append(username) 
				known_face_encodings.append(face_encoding) 
			else:
				logger.warning(f"Failed to retrieve or decode face encoding for {username}")

		return known_face_names, known_face_encodings  # Return the collected names and encodings

	async def read_webcam(self):
		"""
		Continuously reads frames from the webcam, detects faces, checks for known faces,
		and handles access accordingly. It resets denial records based on a predefined interval.
		"""
		# Load known face encodings and names
		known_face_names, known_face_encodings = await self.get_known_encodings()
		frame_count = 0 

		while True:
			current_time = time()
			# Reset denial record after the specified interval
			# This is to stop the denial record from growing too big 
            # Probably not needed for demonstration purposes 
			if current_time - self.last_reset_time > self.reset_interval:
				self.denial_record.clear()
				self.last_reset_time = current_time

			# Read a frame from the webcam
			ret, frame = self.cap.read()
			if not ret:
				continue  # Skip the loop if frame is not read correctly

			# Increment frame counter and skip frames based on the specified frame skip value
			frame_count += 1
			if frame_count % self.frame_skip != 0:
				continue  # Skip processing for this frame

			# Resize the frame to reduce resolution and speed up face processing
			small_frame = cv.resize(frame, (0, 0), fx=0.5, fy=0.5)

			# Convert the frame to RGB for face recognition processing
			rgb_frame = cv.cvtColor(small_frame, cv.COLOR_BGR2RGB)
			# Detect faces and their encodings in the frame
			face_locations = face_recognition.face_locations(rgb_frame)
			face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

			# Process each face found
			for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
				# Scale face locations back up to the original frame size
				top *= 2; right *= 2; bottom *= 2; left *= 2

				# Compare face encodings against known faces
				matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
				face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
				# Identify the closest match with the smallest distance
				best_match_index = np.argmin(face_distances) if matches else -1
				name = known_face_names[best_match_index] if best_match_index != -1 and face_distances[best_match_index] < self.threshold else "Unknown"

				# Handle unrecognized or failed matches
				if name == "Unknown" or not any(matches):
					self.handle_denial(frame, top, right, bottom, left, current_time)

				# Draw a label and bounding box around the face
				self.draw_label(frame, name, top, right, bottom, left)

			cv.imshow('Video', frame)
			if cv.waitKey(1) & 0xFF == ord('q'):
				break

		self.cap.release()
		cv.destroyAllWindows()

	def handle_denial(self, frame, top, right, bottom, left, current_time):
		"""
		Handles an access denial by recording the denial once per configured interval in seconds 
		and capturing an image of the denial if it's the first in the interval.
		"""
		interval_key = int(current_time // self.denial_interval)  # Use configured intervals as keys
		if interval_key not in self.denial_record:
			self.denial_record[interval_key] = True
			self.capture_denial_image(frame)

	def capture_denial_image(self, frame):
		"""
		Captures the entire frame when access is denied and saves it with a timestamp.
		"""
		# Generate a timestamp for the filename
		timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
		filename = f"{timestamp}.png" 

		# Save image 
		denied_image_path = os.path.join(self.access_denied_images_path, filename)
		cv.imwrite(denied_image_path, frame)

	def draw_label(self, frame, name, top, right, bottom, left):
		"""
		Draws a labeled bounding box around a detected face in the frame. 
		The box color indicates recognition status.
		"""
		box_color = (0, 0, 255) if name == "Unknown" else (0, 255, 0)
		cv.rectangle(frame, (left, top), (right, bottom), box_color, 2)
		font = cv.FONT_HERSHEY_DUPLEX
		cv.putText(frame, name, (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)

async def main():
	reader = WebcamReader()
	await reader.read_webcam()