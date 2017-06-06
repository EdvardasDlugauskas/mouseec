from collections import defaultdict

import io

import logging
from eyed3.mp3 import Mp3AudioFile
from eyed3 import compat

from os.path import basename

from kivy.core.image import Image as CoreImage
from kivy.uix.image import AsyncImage


class AudioFile(Mp3AudioFile):
	params = defaultdict(lambda: 0)  # default value for any is 3
	_kivy_img = None

	def __init__(self, path):
		self.name, self.extension = basename(path).rsplit(".", maxsplit=1)
		super().__init__(path)

		try:
			if self.images:
				self._kivy_img = CoreImage(io.BytesIO(self.images[0].image_data), ext="jpg")
		except Exception as e:
			logging.warning(e)

	@property
	def bitrate_str(self):
		return self.info.bit_rate_str

	@property
	def bitrate(self):
		return self._info.bit_rate[1] #int(self.bitrate_str.split(" ")[0])

	@property
	def sample_freq_str(self):
		try:
			return str(self.info.sample_freq/1000) + " KHz"
		except KeyError:
			return "unknown frequency"

	@property
	def images(self):
		try:
			return self.tag.images._fs[b'APIC'] or []
		except:
			return []

	@property
	def kivy_image(self):
		return self._kivy_img


	@property
	def kivy_images(self):
		try:
			images = []
			for image in self.images:
				data = io.BytesIO(image.image_data)
				images.append(AsyncImage(data=data, ext="png"))

			return images
		except KeyError:
			return None

	@property
	def date(self):
		#TODO: change this to a relevant date
		try:
			return self.tag.best_release_date
		except AttributeError:
			return None


	def __repr__(self):
		return f"{self.name} \n bitrate: {self.bitrate_str}; frequency: {self.sample_freq_str}; {len(self.images)}" \
		       f" image(s). Date: {self.date}"

if __name__ == "__main__":
	a = AudioFile("lololo\\Caravan Palace - Wonderland.mp3")

	print(f"{a.name}, {a.extension}, has bitrate of {a.bitrate_str} and frequency {a.sample_freq_str}")