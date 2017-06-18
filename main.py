import logging
import os
import threading

import time
from kivy.config import Config
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.widget import WidgetException
from kivymd.snackbar import Snackbar

from utils import call_control, path_select_dialog, timeit
from main_widgets import SmartScrollview

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.properties import ListProperty, ObjectProperty, StringProperty, OptionProperty

from kivymd.theming import ThemeManager

from audiofile import AudioFile, Audio
from moods import Mood

class MeuseeApp(App):
	theme_cls = ThemeManager()

	MUSIC_PATH = StringProperty(".")
	MOODS = ListProperty([Mood("Dark"), Mood("Light"), Mood("Chillax")])

	AUDIOS = ListProperty([])  # (AUDIO_FILE, AUDIO_ENTRY)

	main_screen = ObjectProperty(None)

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

	def build(self):
		self.theme_cls.theme_style = 'Dark'
		self.set_paths()
		self.main_screen = MainScreen()

		self.main_screen.populate()

		return self.main_screen

	def build_config(self, config):
		config.setdefaults('paths', {
			'MUSIC_PATH': '.'
		})

	def set_paths(self):
		config = self.config
		self.MUSIC_PATH = config.get("paths", "MUSIC_PATH")

	def get_audio_entries(self, force=False, thread=None):
		if self.AUDIOS and not force:
			return

		new_audios = []
		for file in os.listdir(self.MUSIC_PATH):
			if file.lower().endswith(".mp3"):
				audio_file = AudioFile(os.path.join(self.MUSIC_PATH, file))
				new_audios.append(Audio(audio_file))
		self.AUDIOS = new_audios

		if thread:
			thread.join()

	def save_path_configuration(self):
		config = self.config
		config.set("paths", "MUSIC_PATH", self.MUSIC_PATH)
		config.write()


class MainScreen(RelativeLayout):
	def populate(self):
		self.ids.all_songs.ids.name_scroll.populate_self()


class AudioListScroller(SmartScrollview):
	"""
	A scrollable MDList for AudioEntry widgets.
	"""

	search_filter_event = None
	is_filter_on = False
	entry_list = ObjectProperty(None)
	root = ObjectProperty(None)
	audio_display_mode = OptionProperty("none",
	                              options=["none", "date", "bitrate", "moods", "images"])

	second_thread = None

	# Default value is to get an event even if the new audio list is []
	audios_to_display = ListProperty([None])

	filters = {
		"none": lambda x: True,
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
			     text="All",
			     on_release=lambda: self.filter_by("none")),
			dict(viewclass="MDMenuItem",
			     text="New",
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

	def populate_self(self):
		threading.Thread(target=self.get_audio_threaded).start()

	def get_audio_threaded(self, *args):
		self.second_thread = threading.Thread(target=lambda: self.current_app.get_audio_entries(force=True), group=None)
		self.second_thread.start()

		self.current_app.root.ids.all_songs.ids.spinner.active = True
		while self.second_thread.is_alive():
			time.sleep(0.2)
		self.current_app.root.ids.all_songs.ids.spinner.active = False

		Clock.schedule_once(self.join_and_continue)

	@mainthread
	def join_and_continue(self, dt):
		self.second_thread.join()

		def temp(dt):
			self.audio_display_mode = "none"
			self.audios_to_display = self.all_audio_files
			self.current_app.root.ids.all_songs.ids.spinner.active = False

		Clock.schedule_once(temp)

	@property
	def all_audio_files(self):
		return self.current_app.AUDIOS

	def refresh(self):
		self.ids.entry_list.clear_widgets()
		self.get_audio_threaded()
		self.audios_to_display = self.all_audio_files
		Snackbar(text="Refreshed.", duration=2, y=60).show()

	@mainthread
	def filter_by(self, by, reverse=False):
		self.audio_display_mode = by
		self.audios_to_display = sorted(self.all_audio_files, key=self.filters[by], reverse=reverse)
		Snackbar(text="Filtered.", duration=1, y=60).show()

	def run_search_countdown(self, text):
		# initializes to "" which changes audios_to_display
		if self.search_filter_event:
			self.search_filter_event.cancel()

		self.search_filter_event = Clock.schedule_once(lambda *x: self.search_filter(text), 0.7)

	def search_filter(self, text):
		self.audios_to_display = list(filter(lambda x: text.lower() in x.file.name.lower(), self.all_audio_files))

	def on_audio_display_mode(self, *args):
		self.on_audios_to_display("", "")

	@mainthread
	def on_audios_to_display(self, *args):
		logging.info("`audios_to_display` has changed to " + str(args[1]))

		self.ids.entry_list.clear_widgets()

		Clock.schedule_once(lambda *x: self.load_extra_entries(n=30, no_scroll=True))


	@call_control(max_call_interval=0.3)
	@mainthread
	def load_extra_entries(self, n=10, no_scroll=False):
		logging.info(f"Loading extra {n} entries")
		previous_height = self.ids.entry_list.height

		to_load = []

		index = 0
		count = 0
		try:
			while count < n and index < len(self.audios_to_display):
				if not self.audios_to_display[index].widget.parent:
					to_load.append(self.audios_to_display[index].widget)
					count += 1
				index += 1
		except IndexError:
			logging.info("No more entries to load.")

		logging.info(f"Entries to load: {to_load}")
		for entry in to_load:
			try:
				entry.display_mode = self.audio_display_mode
				self.ids.entry_list.add_widget(entry)
			except WidgetException:  # scrolled too fast - kivy bug?
				logging.warning(f"Adding a widget skipped. Scrolled too fast? Widget: {entry}, parent: {entry.parent}")

		if not no_scroll:
			current_height = self.ids.entry_list.height
			self.scroll_y += self.convert_distance_to_scroll(0, current_height - previous_height)[1]
		else:
			self.scroll_y = 1

	def open_folder_select_dialog(self):
		path_select_dialog(self)


if __name__ == "__main__":
	MeuseeApp().run()
