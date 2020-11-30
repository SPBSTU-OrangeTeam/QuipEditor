import sublime
import sublime_plugin
from .src.providers import quip_provider
from .CurrentManager import CurrentManager
import os


current = CurrentManager()


class OpenRecentDocumentCommand(sublime_plugin.WindowCommand):
	def run(self):
		view = self.window.new_file()
		view.run_command("insertrandomdocumenthtml")

class ShowFileTreeCommand(sublime_plugin.WindowCommand):
	def run(self):
		view = self.window.new_file()
		view.run_command("printquipfiletree")

class InsertrandomdocumenthtmlCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		quipprovider = quip_provider.QuipProvider()
		thread_ids = quipprovider.get_document_thread_ids()
		id = thread_ids.pop()
		current.add(view=self.view, thread=id)
		self.view.insert(edit, 0, quipprovider.get_document_content(id))

class OpenChatCommand(sublime_plugin.WindowCommand):

	quip = quip_provider.QuipProvider()
	
	def __init__(self, window):
		super().__init__(window)

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
				self.chat.set_scratch(True)
				self.window.run_command('close')
			return

		self.window.run_command('set_layout', {
			"cols": [0, 0.70, 1.0],
			"rows": [0.0, 1.0],
			"cells": [[0, 0, 1, 1], [1, 0, 2, 1]]
		})
		self.__open_chat()

	def __open_chat(self):
		self.__load_recent_chats()
		self.__load_chat_messages()
		self.toggled = True
		self.chat = sublime.active_window().new_file()

		self.chat.settings().set('auto_indent', False)
		self.chat.run_command("insert", {"characters": '\n'.join(self.chat_messages)})
		self.chat.settings().erase('auto_indent')
		
		self.chat.set_name(self.chat_name)
		self.chat.set_read_only(True)
		current.set_chat(self.chat_id, self.chat)

	def __load_recent_chats(self):
		chats = self.quip.get_recent_chats()
		self.chat_id, self.chat_name = chats.pop()

	def __load_chat_messages(self):
		self.chat_messages = self.quip.get_chat_messages(self.chat_id)


class SendChatMessageCommand(sublime_plugin.TextCommand):
	
	quip = quip_provider.QuipProvider()
	user = quip.current_user()

	def run(self, edit):
		current_window = sublime.active_window()
		if current.chat:
			current_window.show_input_panel('Enter chat message:', '', self.__send_message, None, None)

	def __send_message(self, message):
		messsage = self.user.get("name", "Me") + ': ' + message + '\n'
		# Тут надо вставить сообщение в чат
		self.quip.new_message(current.chat_id, message)


class Printquipfiletree(sublime_plugin.TextCommand):
	def __print_tree(self, tree_node, prefix):
		if tree_node is None:
			return ""
		str_result = '{0} Name: {1} | Type: {2}\n'.format(prefix, tree_node.name, tree_node.thread_type)
		if tree_node.children is None:
			return str_result
		for child in tree_node.children:			
			str_result += self.__print_tree(child, prefix+"-")
		return str_result

	def run(self, edit):
		quipprovider = quip_provider.QuipProvider()
		file_tree = quipprovider.get_thread_tree()
		string_tree = self.__print_tree(file_tree, "")
		self.view.insert(edit, 0, string_tree)


class UploadChangesOnSave(sublime_plugin.EventListener):
	
	def on_pre_save(self, view):
		if not current.contains(view=view):
			return

		quip = quip_provider.QuipProvider()
		line = view.substr(view.full_line(view.sel()[0]))
		if line.startswith('<') and line.endswith('>\n'):
			html = line
		else:
			html = "<p>" + line + "</p>"

		quip.edit_document(thread_id=current.get(view), content=html)
