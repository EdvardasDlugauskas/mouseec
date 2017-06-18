import time

import logging
from kivy.uix.popup import Popup
from os import path

from libs.garden.filebrowser import FileBrowser


def browser_selection(instance: FileBrowser):
	if not instance.selection:
		# If nothing is selected, choose current dir
		selection = instance.path
	else:
		selection = instance.selection[0]

	return selection


def timeit(method):
	def timed(*args, **kw):
		ts = time.time()
		result = method(*args, **kw)
		te = time.time()

		if 'log_time' in kw:
			name = kw.get('log_name', method.__name__.upper())
			kw['log_time'][name] = int((te - ts) * 1000)
		else:
			print('%r  %2.2f ms' % \
			      (method.__name__, (te - ts) * 1000))
		return result

	return timed


class cached_property:
	"""
	Descriptor (non-data) for building an attribute on-demand on first use.
	"""

	def __init__(self, factory):
		"""
		<factory> is called such: factory(instance) to build the attribute.
		"""
		self._attr_name = factory.__name__
		self._factory = factory

	def __get__(self, instance, owner):
		# Build the attribute.
		attr = self._factory(instance)

		# Cache the value; hide ourselves.
		setattr(instance, self._attr_name, attr)

		return attr


def path_select_dialog(instance):
	popup = Popup(size_hint=(.9, .9), title="Select music path")

	browser = FileBrowser(select_string='Save', dirselect=True,
	                      show_hidden=False, filters=["!.sys"])

	default_path = instance.current_app.MUSIC_PATH
	if path.exists(default_path):
		browser.path = default_path

	def success(fb):
		logging.info("Changed music path to " + browser_selection(browser))
		instance.current_app.MUSIC_PATH = browser_selection(browser)
		popup.dismiss()
		instance.refresh()
		instance.current_app.save_path_configuration()

	browser.bind(on_success=success,
	             on_canceled=popup.dismiss)

	popup.content = browser
	popup.open()


class call_control:
	def __init__(self, max_call_interval):
		self._max_call_interval = max_call_interval
		self._last_call = time.time()

	def __call__(self, func):
		def wrapped(*args, **kwargs):
			now = time.time()

			if now - self._last_call > self._max_call_interval:
				self._last_call = now

				func(*args, **kwargs)

		return wrapped
