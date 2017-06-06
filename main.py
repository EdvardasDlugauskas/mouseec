import logging
import os
import threading

from kivy.config import Config
from kivy.uix.relativelayout import RelativeLayout

from utils import call_control, path_select_dialog
from widgets import Audio, SmartScrollview

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivy.app import App
from kivy.clock import Clock
from kivy.properties import ListProperty, ObjectProperty, StringProperty

from kivymd.theming import ThemeManager

from audiofile import AudioFile


class MeuseeApp(App):
	theme_cls = ThemeManager()

	MUSIC_PATH = StringProperty(".")
	PARAMS = ListProperty(["Dark", "Light", "Chillax"])

	AUDIOS = ListProperty([])  # (AUDIO_FILE, AUDIO_ENTRY)

	main_screen = ObjectProperty(None)

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

	def build(self):
		self.theme_cls.theme_style = 'Dark'
		self.set_paths()
		self.main_screen = MainScreen()

		return self.main_screen

	def build_config(self, config):
		config.setdefaults('paths', {
			'MUSIC_PATH': '.'
		})

	def set_paths(self):
		config = self.config
		self.MUSIC_PATH = config.get("paths", "MUSIC_PATH")

	def force_get_audio_entries(self):
		new_audios = []
		for file in os.listdir(self.MUSIC_PATH):
			if file.lower().endswith(".mp3"):
				audio_file = AudioFile(os.path.join(self.MUSIC_PATH, file))
				new_audios.append(Audio(audio_file))
		self.AUDIOS = new_audios

	def save_path_configuration(self):
		config = self.config
		config.set("paths", "MUSIC_PATH", self.MUSIC_PATH)
		config.write()


class MainScreen(RelativeLayout):
	pass


class AudioListScroller(SmartScrollview):
	"""
	A scrollable MDList for AudioEntry widgets.
	"""

	search_filter_event = None
	is_filter_on = False
	entry_list = ObjectProperty(None)
	# all_audio_files = []

	# Default value is to get an event even if the new audio list is []
	audios_to_display = ListProperty([1])

	filters = {
		"bitrate": lambda x: x.file.bitrate,
		"moods": lambda x: sum(x.file.params.values()),
		"images": lambda x: len(x.file.images),
		"date": lambda x: x.file.date or 0
	}

	def __init__(self, **kw):
		super().__init__(**kw)
		self.options_menu_items = [
			dict(viewclass="MDMenuItem",
			     text="Refresh",
			     on_release=self.refresh),
			dict(viewclass="MDMenuItem",
			     text="Select Folder",
			     on_release=self.open_folder_select_dialog)]
		self.filter_menu_items = [
			dict(viewclass="MDMenuItem",
			     text="New Songs",
			     on_release=lambda: self.filter_by("date", reverse=True)),
			dict(viewclass="MDMenuItem",
			     text="Low Bitrate",
			     on_release=lambda: self.filter_by("bitrate")),
			dict(viewclass="MDMenuItem",
			     text="Few Moods",
			     on_release=lambda: self.filter_by("moods")),
			dict(viewclass="MDMenuItem",
			     text="No Images",
			     on_release=lambda: self.filter_by("images"))]
		self.current_app = App.get_running_app()
		Clock.schedule_once(self.post_init)

	def post_init(self, dt):
		self.entry_list = self.ids.entry_list

		thread = threading.Thread(target=self.current_app.force_get_audio_entries, group=None)
		thread.start()
		thread.join()

	@property
	def all_audio_files(self):
		return self.current_app.AUDIOS

	def refresh(self):
		for audio in self.all_audio_files:
			if audio._widget:
				self.ids.entry_list.remove_widget(audio.get_widget())

		self.current_app.force_get_audio_entries()
		self.audios_to_display = self.current_app.AUDIOS

	def filter_by(self, by, reverse=False):
		self.audios_to_display = sorted(self.all_audio_files, key=self.filters[by], reverse=reverse)

	def run_search_countdown(self, text):
		if self.search_filter_event:
			self.search_filter_event.cancel()

		self.search_filter_event = Clock.schedule_once(lambda *x: self.search_filter(text), 0.7)

	def search_filter(self, text):
		self.audios_to_display = list(filter(lambda x: text.lower() in x.file.name.lower(), self.all_audio_files))

	def on_audios_to_display(self, *args):
		current_app = App.get_running_app()
		current_app.root.ids.spinner.active = True
		logging.info("`audios_to_display` has changed to " + str(args[1]))

		for audio in self.all_audio_files:
			if audio._widget:
				self.ids.entry_list.remove_widget(audio.get_widget())

		self.load_extra_entries(20)
		current_app.root.ids.spinner.active = False
		self.scroll_y = 1

	@call_control(max_call_interval=0.1)
	def load_extra_entries(self, n=9):
		logging.info(f"Loading extra {n} entries")
		previous_height = self.ids.entry_list.height

		to_load = []

		index = 0
		count = 0
		try:
			while count < n and index < len(self.audios_to_display):
				if not self.audios_to_display[index].get_widget().parent:
					to_load.append((self.audios_to_display[index].get_widget()))
					count += 1
				index += 1
		except IndexError:
			logging.info("No more entries to load.")

		for entry in to_load:
			self.ids.entry_list.add_widget(entry)

		current_height = self.ids.entry_list.height
		self.scroll_y += self.convert_distance_to_scroll(0, current_height - previous_height)[1]

	def open_folder_select_dialog(self):
		path_select_dialog(self)


if __name__ == "__main__":
	MeuseeApp().run()
