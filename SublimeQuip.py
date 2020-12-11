import sublime
import sublime_plugin
import json
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
				self.window.run_command('close')
			current.reset_chat()
			return

		self.window.run_command('set_layout', {
			"cols": [0, 0.70, 1.0],
			"rows": [0.0, 1.0],
			"cells": [[0, 0, 1, 1], [1, 0, 2, 1]]
		})
		self.__open_chat()

	def __open_chat(self):
		self.__load_recent_chats()
		self.toggled = True
		self.chat = sublime.active_window().new_file()	
		current.set_chat(self.chat_id, self.chat)
		self.chat.run_command("insert_chat_messages", {"messages": [str(m) for m in self.quip.get_messages(self.chat_id)]})
		self.chat.set_name(self.chat_name)

	def __load_recent_chats(self):
		chats = self.quip.get_recent_chats()
		self.chat_id, self.chat_name = chats.pop()


class InsertChatMessagesCommand(sublime_plugin.TextCommand):

	quip = quip_provider.QuipProvider()

	def run(self, edit, messages):
		result = '\n'.join(messages)
		current.chat.set_scratch(False)
		current.chat.set_read_only(False)
		self.view.insert(edit, self.view.size(), result)
		current.chat.set_read_only(True)
		current.chat.set_scratch(True)



class SendChatMessageCommand(sublime_plugin.TextCommand):
	
	def run(self, edit):
		current_window = sublime.active_window()
		if current.chat:
			current_window.show_input_panel('Enter chat message:', '', self.__send_message, None, None)

	def __send_message(self, text: str):
		quip = quip_provider.QuipProvider()
		message = quip.send_message(current.chat_id, text)
		current.chat.run_command("insert_chat_messages", {"messages": [str(message)]})


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


# Section with test commands!

class ShowTestChatCommand(sublime_plugin.WindowCommand):
	def run(self, **args):
		view = self.window.new_file()
		view.run_command("insert_test_chat")

class ShowTestContactsCommand(sublime_plugin.WindowCommand):
	def run(self, **args):				
		view = self.window.new_file()
		view.run_command("insert_test_contacts")

def on_message(ws, message):
    print("message:")
    print(json.dumps(json.loads(message), indent=4))

def on_error(ws, error):
    print("error:")
    print(error)

def on_close(ws):
    print("### connection closed ###")

class OpenTestWebsocketCommand(sublime_plugin.WindowCommand):
	def run(self, **args):				
		quipprovider = quip_provider.QuipProvider()
		# Not working because ssl lib obsolete
		quipprovider.subscribe_messages(on_message=on_message, on_error=on_error, on_close=on_close)

class InsertTestContactsCommand(sublime_plugin.TextCommand):
	def __print_user(self, user):
		# images does not work (need to investigate)
		return "<div><img src=\"file://%s\" alt=\"n/a\"><span>%s</span></div>" % (user.profile_picture_path, user.name)

	def run(self, edit):
		string_tree = ""
		quipprovider = quip_provider.QuipProvider()
		user, friend_list = quipprovider.get_contacts()
		string_tree += self.__print_user(user)
		string_tree += "<ul>"
		for friend in friend_list:
			string_tree += "<li>%s</li>" % self.__print_user(friend)
		string_tree += "</ul>"
		phantom = sublime.Phantom(
			region = self.view.visible_region(),
			content = string_tree,
			layout = sublime.LAYOUT_INLINE
		)
		sublime.PhantomSet(self.view, "chat_phantom_set").update([phantom, phantom])

class InsertTestChatCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		quipprovider = quip_provider.QuipProvider()
		user, friend_list = quipprovider.get_contacts()
		friend = friend_list.pop()
		str_result = ""
		for message in quipprovider.get_messages(friend.chat_thread_id):
			str_result += "%s | %s [%s]%s: %s\n" % (message.author_id, 
				message.author_name, message.timestamp, " (edited)" if message.edited else "", message.text)
		self.view.insert(edit, 0, str_result)
