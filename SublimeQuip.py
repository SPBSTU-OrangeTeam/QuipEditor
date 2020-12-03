import sublime
import sublime_plugin
import json
import os

from .src.providers import quip_provider
from .CurrentManager import CurrentManager
from .TabsManager import TabsManager
from .TabsManager import FILE_TREE_TAB_ID


COMMAND_OPEN_DOCUMENT = "open_recent_document"
COMMAND_PRINT_QUIP_FILE_TREE = "print_quip_file_tree"
COMMAND_GET_SELECTED_DOCUMENT = "insert_selected_document"
COMMAND_GET_RANDOM_DOCUMENT = "insert_random_document_html"

KEY_THREAD_ID = "thread_id"
KEY_FILE_TREE_PHANTOM_SET = "file_tree_phantom_set"

current = CurrentManager()
tabs_manager = TabsManager()

class OpenRecentDocumentCommand(sublime_plugin.WindowCommand):
	def run(self, **args):
		if args is not None and KEY_THREAD_ID in args.keys():
			thread_id = args[KEY_THREAD_ID]
			if tabs_manager.contains_tab(thread_id):
				view = tabs_manager.get_tab(thread_id)
				self.window.focus_view(view)
			else:
				view = self.window.new_file()
				tabs_manager.add_tab(thread_id, view)
			view.run_command(COMMAND_GET_SELECTED_DOCUMENT, args)
		else:
			view = self.window.new_file()
			view.run_command(COMMAND_GET_RANDOM_DOCUMENT)

class ShowFileTreeCommand(sublime_plugin.WindowCommand):
	def run(self):
		if not tabs_manager.contains_tab(FILE_TREE_TAB_ID):
			view = self.window.new_file()
			tabs_manager.add_tab(FILE_TREE_TAB_ID, view)
		else:
			view = tabs_manager.get_tab(FILE_TREE_TAB_ID)
			self.window.focus_view(view)
		view.run_command(COMMAND_PRINT_QUIP_FILE_TREE)

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

class InsertRandomDocumentHtmlCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		quipprovider = quip_provider.QuipProvider()
		thread_ids = quipprovider.get_document_thread_ids()
		id = thread_ids.pop()
		current.add(view=self.view, thread=id)
		self.view.insert(edit, 0, quipprovider.get_document_content(id))

class InsertSelectedDocumentCommand(sublime_plugin.TextCommand):
	def run(self, edit, **args):
		doc_id = args[KEY_THREAD_ID]
		assert doc_id is not None
		quipprovider = quip_provider.QuipProvider()
		current.add(view=self.view, thread=doc_id)
		self.view.replace(edit, self.view.visible_region(), quipprovider.get_document_content(doc_id))

class PrintQuipFileTree(sublime_plugin.TextCommand):
	def __print_tree(self, tree_node, prefix, postfix):
		if tree_node is None:
			return ""
		thread_name = tree_node.name
		if tree_node.thread_type == 'document':
			thread_name = '<a href=\'{0}\'>{1}</a>'.format(tree_node.thread_id, tree_node.name)
		str_result = '{0} Name: {1} | Type: {2}{3}'.format(
			prefix,
			thread_name,
			tree_node.thread_type,
			postfix
		)
		if tree_node.children is None:
			return str_result
		for child in tree_node.children:
			str_result += '<ul>'
			str_result += self.__print_tree(child, "<li>", "</li>")
			str_result += '</ul>'
		return str_result

	def run(self, edit):
		self.view.erase_phantoms(KEY_FILE_TREE_PHANTOM_SET)
		self.view.set_read_only(True)
		self.view.set_name("Folders")
		quipprovider = quip_provider.QuipProvider()
		file_tree = quipprovider.get_thread_tree()
		string_tree = self.__print_tree(file_tree, "", "")
		phantom = sublime.Phantom(
			region = self.view.visible_region(),
			content = string_tree,
			layout = sublime.LAYOUT_INLINE,
			on_navigate = self.__open_doc
		)
		sublime.PhantomSet(self.view, KEY_FILE_TREE_PHANTOM_SET)\
			.update([phantom, phantom]) #TODO разобраться почему только так работает

	def __open_doc(self, doc_id):
		self.view.window().run_command(COMMAND_OPEN_DOCUMENT, {KEY_THREAD_ID: doc_id})


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
	def on_pre_close(self, view):
		tabs_manager.remove_tab_by_view(view)
#Section with test commands!




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
