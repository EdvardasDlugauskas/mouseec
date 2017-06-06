import logging

from kivy.app import App
from kivy.effects.dampedscroll import DampedScrollEffect
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivymd.dialog import MDDialog
from kivymd.grid import SmartTile
from kivymd.label import MDLabel
from kivymd.list import ILeftBody, IRightBody, OneLineAvatarIconListItem, MDList
from kivymd.menu import MDDropdownMenu

from utils import call_control


class Audio:
	_widget = None

	def __init__(self, file):
		self.file = file

	def get_widget(self):
		if not self._widget:
			logging.info(f"Loading new AudioEntry for {self.file.name}")
			self._widget = AudioEntry(self.file)
		return self._widget


class ParamGridLayout(GridLayout):
	pass


class ParamLabel(MDLabel):
	pass


class SmartScrollEffect(DampedScrollEffect):
	spring_constant = 5

	def on_overscroll(self, *args):
		super().on_overscroll(*args)
		if 100 > self.overscroll > 0:
			self.load_new_entries()
		if self.overscroll < -500:
			self.target_widget.parent.scroll_y = 1

	@call_control(max_call_interval=0.1)
	def load_new_entries(self):
		App.get_running_app().main_screen.ids.name_scroll.load_extra_entries()


class SmartScrollview(ScrollView):
	effect_cls = SmartScrollEffect

	def on_scroll_y(self, *args):
		if self.scroll_y < 0.02:
			self.load_extra_entries()


class LeftAvatar(ILeftBody, Image):
	pass


class RightIconBox(BoxLayout, IRightBody):
	pass


class AudioEntry(OneLineAvatarIconListItem):
	def __init__(self, audio_file, **kwargs):
		super().__init__(**kwargs)
		self.audio_file = audio_file
		self.text = audio_file.name  # audio_file.name
		self.secondary_text = str(dict(self.audio_file.params)).replace("{", "").replace("}", "")

		if audio_file.kivy_image:
			self.ids.avatar.texture = audio_file.kivy_image.texture

		self.menu_items = [
			dict(viewclass="MDMenuItem",
			     text="Edit",
			     on_release=self.edit),
			dict(viewclass="MDMenuItem",
			     text="Info",
			     on_release=self.info_dialog),
		]

		right_box = RightIconBox()
		bitrate = self.audio_file.bitrate
		if bitrate < 150:
			right_box.add_widget(MDLabel(text=self.audio_file.bitrate_str, text_color=(1, 0.2, 0.2, 0.7),
			                             theme_text_color="Custom", font_style="Body1", size_hint_x=None, width=35))

		elif bitrate < 250:
			right_box.add_widget(MDLabel(text=self.audio_file.bitrate_str, theme_text_color="Hint",
			                             font_style="Body1", size_hint_x=None, width=35))

		self.add_widget(right_box)

	def on_touch_up(self, touch):
		super().on_touch_up(touch)
		if self.collide_point(*touch.pos) and touch.grab_current is not None:
			if touch.device == "mouse" and touch.button == "right":
				MDDropdownMenu(items=self.menu_items, width_mult=2).open(touch, touch=True)

	def edit(self):
		print(self.height)
		print("Editing")

	def info_dialog(self):
		content = MDList()
		label = MDLabel(font_style='Subhead', theme_text_color='Secondary',
		                text="\n" + str(self.audio_file), valign='center', halign="center")
		label.bind(texture_size=label.setter('size'))

		image = SmartTile(allow_stretch=True, keep_ratio=True, box_color=[0, 0, 0, 0], size_hint_y=None, height=300)
		image._img_widget.texture = self.ids.avatar.texture

		content.add_widget(image)
		content.add_widget(label)

		self.dialog = MDDialog(title=self.audio_file.name, content=content, size_hint=(.8, 0.75),
		                       auto_dismiss=False)

		self.dialog.add_action_button("Dismiss",
		                              action=lambda *x: self.dialog.dismiss())
		self.dialog.open()
