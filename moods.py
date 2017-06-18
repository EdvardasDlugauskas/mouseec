from kivy.app import App
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivymd.button import MDIconButton
from kivymd.tabs import MDBottomNavigationItem, MDTab

moods_icons = """emoticon
emoticon-cool 
emoticon-dead
emoticon-devil
emoticon-excitedB
emoticon-happy
emoticon-neutral6
emoticon-poop
emoticon-sad
emoticon-tongue
brightness-5
fire
ghost
umbrella-outline
yin-yang
weather-rainy
weather-lightning-rainy
vk-box"""

MDIconButton

class Mood:
	def __init__(self, mood_name, icon_name="ghost"):
		self.name = mood_name
		self.icon_name = icon_name

class MoodTab(MDTab):
	def __init__(self, mood, **kwargs):
		self.mood = mood
		self.icon = mood.icon_name
		super().__init__(**kwargs)

		Clock.schedule_once(self.post_init)

	def post_init(self, dt):
		key = lambda x: self.mood in x.file.moods
		all_audios = App.get_running_app().AUDIOS
		self.ids.scroller.audios_to_display = sorted(filter(key, all_audios), key=key)


class MoodsScreen(MDBottomNavigationItem):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.current_app = App.get_running_app()

		Clock.schedule_once(self.post_init)

	def post_init(self, dt):
		moods = self.current_app.MOODS
		for mood in moods:
			self.ids.mood_tabs.add_widget(MoodTab(mood, name=mood.name, text=mood.name))
