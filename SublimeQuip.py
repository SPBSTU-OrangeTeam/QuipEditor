import sublime
import sublime_plugin
from .src.providers import quip_provider

import os

global comments
comments = sublime.cache_path() + '/QUIP'
if not os.path.exists(comments):
    os.makedirs(comments)
comments += '/chat.qcht'
with open(comments, 'w+') as chat:
	pass



class OpenRecentDocumentCommand(sublime_plugin.WindowCommand):
	def run(self):
		view = self.window.new_file()
		view.run_command("insertrandomdocumenthtml")

class InsertrandomdocumenthtmlCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		quipprovider = quip_provider.QuipProvider()
		thread_ids = quipprovider.get_document_thread_ids()
		self.view.insert(edit, 0, quipprovider.get_document_content(thread_ids.pop()))


class OpenChatCommand(sublime_plugin.WindowCommand):
	def run(self):
		if hasattr(self, 'toggled') and self.toggled:
			self.window.run_command('set_layout', {
				"cols": [0, 1.0],
				"rows": [0.0, 1.0],
				"cells": [[0, 0, 1, 1]]
			})
			self.toggled = False
			self.window.focus_view(self.chat)
			if self.window.active_view() == self.chat:
				self.window.run_command('close')
			return

		self.window.run_command('set_layout', {
			"cols": [0, 0.70, 1.0],
			"rows": [0.0, 1.0],
			"cells": [[0, 0, 1, 1], [1, 0, 2, 1]]
		})
		self.toggled = True
		self.chat = sublime.active_window().open_file(comments)
		self.chat.set_name('Chat name')
		self.chat.set_read_only(True)


class SendChatMessageCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		current_window = sublime.active_window()
		current_window.show_input_panel('Сообщение для чата:', '', self._send_message, None, None)

	def _send_message(self, message):
		with open(comments, 'a+') as chat:
			chat.write('User: ' + message + '\n')



