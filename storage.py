from pathlib import Path
import pickle
import asyncio
from io import BytesIO
from typing import Any

from werkzeug.datastructures import FileStorage

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


	async def add_user(self, username: str, io_stream:BytesIO, *args, **kwargs) -> None:
		user_dir = self.get_relative_path(f"known_users/{username}")
		user_dir.mkdir(exist_ok=True, parents=True)
		img_path = user_dir.joinpath("img.jpg")

		with img_path.open("wb") as write_file:
			write_file.write(io_stream.read())

		store = await self.read()
		store[username] = str(img_path)
		await self.write(store)


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
		return list([ (k,v) for k, v in store.items()])
