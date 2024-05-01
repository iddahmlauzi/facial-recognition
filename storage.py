from pathlib import Path
import pickle
import asyncio
import face_recognition
from io import BytesIO
from typing import Any
import os
from cryptography.fernet import Fernet
from werkzeug.datastructures import FileStorage
import numpy as np

class PickleStorage():
	""" Caches data to disk as a pickle for quickly reading/writing/storing small chunks of
	information. """
	default_value=None
	default_id = None

	def __init__(self, *args,  on_create: callable=None, **kwargs):
		if self.default_id:
			self.cache_id = self.default_id
		else:
			self.cache_id = args[0]
		self.on_create = on_create


	@property
	def default_cache_name(self):
		name = getattr(self, 'cache_id', None)
		if not name:
			name = self.__class__.__name__.lower() + '.dat'
			return name

		else:
			return name

	
	def _ensure_path_exists(self, path_obj: Path=None):
		""" Makes sure the target path actually exists on the disk"""

		if not path_obj:
			path_obj = self.get_path_to_cache()

		# Make the directory
		if path_obj.is_dir():
			if not path_obj.exists():
				path_obj.mkdir(parents=True, exist_ok=True)
				return False

			else:
				return True

		# Means the path points to a file, so we want to create the
		# parent directories, as well as the file itself
		else:
			if not path_obj.exists():
				path_obj.parents[0].mkdir(parents=True, exist_ok=True)

				if self.on_create:
					self.on_create(cache=self)
				else:
					asyncio.create_task(
						self.write(self.default_value)
					)
				return False
			else:
				return True


	def get_path_to_cache(self, filename: str=None):
		if not filename:
			return self.get_relative_path(self.default_cache_name)
		else:
			return self.get_relative_path(filename)

		return Path(path_str)


	def get_relative_path(self, path: str):
		return Path(Path(__file__).parent, path)


	async def cache_reset(self, *args, **kwargs):
		await self.write(self.default_value)


	async def read(self, *args, filename: str =None, **kwargs):

		cache_path = self.get_path_to_cache(filename)
		self._ensure_path_exists(cache_path)

		try:
			with Path(cache_path).open('rb') as f:
				d = f.read()
			return pickle.loads(d)

		# Probably means that the file hasn't been written to
		# disc yet
		except (FileNotFoundError, EOFError):
			return self.default_value


	async def write(self, data:Any, *args, filename: str = None, **kwargs):

		cache_path = self.get_path_to_cache(filename)
		self._ensure_path_exists(cache_path)
		with Path(cache_path).open('wb') as f:
			f.write(pickle.dumps(data))


class UserStorage(PickleStorage):
	""" Used to store and retrieve information related to users on the system. """

	default_id = "user_storage.dat"
	default_value = {}
	key_file = 'encryption.key'
	iv_file = 'encryption.iv'
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.load_keys()
	
	def load_keys(self):
		# Check if key and IV exist
		if os.path.exists(self.key_file) and os.path.exists(self.iv_file): 
			with open(self.key_file, 'rb') as keyfile:
				encryption_key = keyfile.read()
			with open(self.iv_file, 'rb') as ivfile:
				self.iv = ivfile.read()
		else:
			# Generate and save new key and IV
			encryption_key = Fernet.generate_key()
			self.iv = os.urandom(16)  # Adjust size according to your encryption algorithm
			with open(self.key_file, 'wb') as keyfile:
				keyfile.write(encryption_key)
			with open(self.iv_file, 'wb') as ivfile:
				ivfile.write(self.iv)
		
		self.fernet = Fernet(encryption_key)

	async def add_user(self, username: str, io_stream: BytesIO, *args, **kwargs) -> None:
			user_dir = self.get_relative_path(f"known_users/{username}")
			user_dir.mkdir(exist_ok=True, parents=True)
			img_path = user_dir.joinpath("img.jpg")

			# Write the image file
			with img_path.open("wb") as write_file:
				io_stream.seek(0)
				write_file.write(io_stream.read())
			
			# Load image to create encoding
			user_image = face_recognition.load_image_file(str(img_path))
			user_image_encoding = face_recognition.face_encodings(user_image)
			if user_image_encoding:
				user_image_encoding = user_image_encoding[0]  # assuming one face per image for simplicity
				# Encrypt the face encoding
				encrypted_encoding = self.fernet.encrypt(user_image_encoding.tobytes())
				encoding_path = user_dir.joinpath("encoding.dat")
				with encoding_path.open("wb") as encoding_file:
					encoding_file.write(encrypted_encoding)
				encoding_path_str = str(encoding_path)
			else:
				encoding_path_str = None

			# Store details in pickle
			store = await self.read()
			store[username] = {
				'img_path': str(img_path),
				'encoding_path': encoding_path_str
			}
			await self.write(store)

	async def get_user_encoding(self, username: str) -> np.ndarray:
		store = await self.read()
		user_info = store.get(username)
		if not user_info or 'encoding_path' not in user_info:
			return None
		
		encoding_path = Path(user_info['encoding_path'])
		if not encoding_path.exists():
			return None
		
		with encoding_path.open('rb') as file:
			encrypted_encoding = file.read()
		
		decrypted_encoding = self.fernet.decrypt(encrypted_encoding)
		face_encoding = np.frombuffer(decrypted_encoding, dtype=np.float64)
		return face_encoding


	async def get_user_image(self, username: str, *args, **kwargs) -> bytes:
		store = await self.read()
		img_path_str = store.get(username, None)
		if not img_path_str:
			return None

		img_path = Path(img_path_str)
		with img_path.open("rb") as f:
			data = f.read()
		return data


	async def list_users(self, *args, **kwargs):
		store = await self.read()
		return [(k, v['img_path'], v['encoding_path']) for k, v in store.items() if 'encoding_path' in v]

