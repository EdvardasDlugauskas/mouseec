from collections import defaultdict

import io
from os.path import basename
import logging

from eyed3.mp3 import Mp3AudioFile
from kivy.core.image import Image as CoreImage
from kivy.uix.image import AsyncImage

from main_widgets import AudioEntry
from utils import cached_property


class Audio:
	_widget = None

	def __init__(self, file):
		self.file = file

	@property
	def widget(self):
		if not self._widget:
			#logging.info(f"Loading new AudioEntry for {self.file.name}")
			self._widget = AudioEntry(self.file)
		return self._widget

class AudioFile(Mp3AudioFile):
	params = defaultdict(lambda: 0)  # default value for any is 3
	_kivy_img = None

	def __init__(self, path):
		self.name, self.extension = basename(path).rsplit(".", maxsplit=1)
		super().__init__(path)
		temp = self.kivy_image

	@cached_property
	def bitrate_str(self):
		return self.info.bit_rate_str

	@cached_property
	def bitrate(self):
		return self._info.bit_rate[1] #int(self.bitrate_str.split(" ")[0])

	@cached_property
	def sample_freq_str(self):
		try:
			return str(self.info.sample_freq/1000) + " KHz"
		except KeyError:
			return "unknown frequency"

	@cached_property
	def images(self):
		try:
			return self.tag.images._fs[b'APIC'] or []
		except:
			return []

	@cached_property
	def kivy_image(self):
		if not self._kivy_img:
			try:
				images = self.images
				if images:
					self._kivy_img = CoreImage(io.BytesIO(images[0].image_data), ext="jpg")
			except Exception as e:
				logging.warning(e)

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

	@property
	def moods(self):
		return sorted(self.params, key=lambda x: x.value())

	def __repr__(self):
		return f"{self.name} \n bitrate: {self.bitrate_str}; frequency: {self.sample_freq_str}; {len(self.images)}" \
		       f" image(s). Date: {self.date}"

if __name__ == "__main__":
	a = AudioFile("original audio files\\Caravan Palace - Wonderland.mp3")

	print(f"{a.name}, {a.extension}, has bitrate of {a.bitrate_str} and frequency {a.sample_freq_str}")

	print("\nFinished successfully.")