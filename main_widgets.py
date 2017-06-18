import logging

from kivy.app import App
from kivy.effects.dampedscroll import DampedScrollEffect
from kivy.effects.scroll import ScrollEffect
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.properties import StringProperty, OptionProperty, ObjectProperty
from kivymd.dialog import MDDialog
from kivymd.grid import SmartTile
from kivymd.label import MDLabel
from kivymd.list import ILeftBody, IRightBody, OneLineAvatarIconListItem, MDList
from kivymd.menu import MDDropdownMenu
from kivymd.tabs import MDTab

from utils import call_control


class ParamGridLayout(GridLayout):
	pass


class ParamLabel(MDLabel):
	pass


class SmartScrollEffect(ScrollEffect):  # (DampedScrollEffect):
	#spring_constant = 10

	def on_overscroll(self, *args):
		# super().on_overscroll(*args)

		if 100 > self.overscroll > 0:
			self.load_new_entries()
		if self.overscroll < -500:
			self.target_widget.parent.scroll_y = 1

	@call_control(max_call_interval=0.1)
	def load_new_entries(self):
		App.get_running_app().main_screen.ids.all_songs.ids.name_scroll.load_extra_entries()


class SmartScrollview(ScrollView):
	effect_cls = SmartScrollEffect

	def on_scroll_y(self, *args):
		if self.scroll_y < 0.07:
			self.load_extra_entries()


class LeftAvatar(ILeftBody, Image):
	pass


class RightIconBox(BoxLayout, IRightBody):
	pass


class AudioEntry(OneLineAvatarIconListItem):
	#label = ObjectProperty(MDLabel(size_hint_x=None, width=35, font_style="Body1"))
	display_mode = StringProperty()

	def __init__(self, audio_file, **kwargs):
		super().__init__(**kwargs)
		self.audio_file = audio_file
		self.text = audio_file.name
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

	def on_display_mode(self, *args):
		text = text_color = ""
		theme_text_color = "Hint"

		if self.display_mode == "bitrate":
			bitrate = self.audio_file.bitrate
			if bitrate < 150:
				text = self.audio_file.bitrate_str
				text_color = (1, 0.2, 0.2, 0.7)
				theme_text_color = "Custom"
			else:
				text = self.audio_file.bitrate_str

		elif self.display_mode == "date":
			text = str(self.audio_file.date)

		elif self.display_mode == "moods":
			text = str(self.audio_file.moods)

		elif self.display_mode == "images":
			text = f"{len(self.audio_file.images)} images"
			theme_text_color = "Hint"

		label = self.ids.label
		label.text = text
		label.theme_text_color = theme_text_color
		label.text_color = text_color if text_color else label.text_color

	def on_touch_up(self, touch):
		super().on_touch_up(touch)
		if self.collide_point(*touch.pos) and touch.grab_current is not None:
			if touch.device == "mouse" and touch.button == "right":
				MDDropdownMenu(items=self.menu_items, width_mult=2).open(touch, touch=True)

	def edit(self):
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
