import sublime
import sublime_plugin
import os
from sublime import Region
from .src.providers import QuipProvider
from .src.managers import TREE_VIEW_TAB_ID, TabsManager
from .src.managers.ChatView import ChatView
from .src.deps.markdownify import markdownify as md


COMMAND_OPEN_DOCUMENT = "open_document"
COMMAND_OPEN_CHAT = "open_chat"
COMMAND_PRINT_QUIP_FILE_TREE = "print_quip_file_tree"
COMMAND_INSERT_SELECTED_DOCUMENT = "insert_selected_document"
COMMAND_INSERT_CHAT_MESSAGES = 'insert_chat_messages'
COMMAND_INSERT_CONTACTS = 'insert_contacts'

KEY_THREAD_ID = "thread_id"
KEY_FILE_TREE_PHANTOM_SET = "file_tree_phantom_set"
KEY_CONTACTS_PHANTOM_SET = "contacts_phantom_set"
KEY_MESSAGES_PHANTOM_SET = "messages_phantom_set"


def plugin_loaded():
	global quip, manager, CACHE_DIRECTORY
	quip = QuipProvider()
	manager = TabsManager()
	CACHE_DIRECTORY = sublime.cache_path() + "/QuipEditor"
	if not os.path.exists(CACHE_DIRECTORY):
		os.makedirs(CACHE_DIRECTORY)


class OpenDocumentCommand(sublime_plugin.WindowCommand):
	def run(self, thread_id):
		view = manager.get_tab(thread_id)
		if not view:
			view = self.window.new_file()
		self.window.focus_view(view)
		view.retarget(CACHE_DIRECTORY + "/" + thread_id + ".html")
		view.run_command(COMMAND_INSERT_SELECTED_DOCUMENT, {"thread_id": thread_id})
		view.run_command('save')
		manager.add(thread_id, view)


class ShowFileTreeCommand(sublime_plugin.WindowCommand):
	def run(self):
		view = manager.get_thread(TREE_VIEW_TAB_ID)
		if not view:
			view = self.window.new_file()
			manager.add(TREE_VIEW_TAB_ID, view)
		self.window.focus_view(view)
		view.run_command(COMMAND_PRINT_QUIP_FILE_TREE)


class InsertSelectedDocumentCommand(sublime_plugin.TextCommand):
	def run(self, edit, thread_id):
		self.view.replace(edit, Region(0, self.view.size()), md(quip.get_document_content(thread_id)))


class PrintQuipFileTree(sublime_plugin.TextCommand):
	def run(self, edit):
		self.view.erase_phantoms(KEY_FILE_TREE_PHANTOM_SET)
		self.view.set_read_only(True)
		self.view.set_name("Folders")
		file_tree = quip.get_thread_tree()
		string_tree = self._print_tree(file_tree, "", "")
		phantom = sublime.Phantom(
			region=Region(0, self.view.size()),
			content=string_tree,
			layout=sublime.LAYOUT_INLINE,
			on_navigate=self._open_doc
		)
		sublime.PhantomSet(self.view, KEY_FILE_TREE_PHANTOM_SET) \
			.update([phantom, phantom])  # TODO разобраться почему только так работает

	def _open_doc(self, doc_id):
		self.view.window().run_command(COMMAND_OPEN_DOCUMENT, {"thread_id": doc_id})

	def _print_tree(self, node, prefix, postfix):
		if node is None:
			return ""
		thread_name = node.name
		if node.thread_type == 'document':
			thread_name = '<a href=\'{0}\'>{1}</a>'.format(node.thread_id, node.name)
		str_result = '{0} Name: {1} | Type: {2}{3}'.format(
			prefix,
			thread_name,
			node.thread_type,
			postfix
		)
		if node.children is None:
			return str_result
		for child in node.children:
			str_result += '<ul>' + self._print_tree(child, "<li>", "</li>") + '</ul>'
		return str_result


class ShowContactsCommand(sublime_plugin.WindowCommand):
	def run(self):
		view = self.window.new_file()
		view.run_command(COMMAND_INSERT_CONTACTS)


class InsertContactsCommand(sublime_plugin.TextCommand):

	def run(self, edit):
		self.view.erase_phantoms(KEY_CONTACTS_PHANTOM_SET)
		self.view.set_read_only(True)
		self.view.set_name("Contacts")

		user, friends = quip.get_contacts()
		if user is None:
			tree = "Пофикси меня"
		else:
			tree = user.__str__()
		tree += "<ul>"
		for friend in friends:
			if user is None:
				tree += "Пофикси меня"
			else:
				tree += "<li>%s</li>" % friend.__str__()
		tree += "</ul>"

		phantom = sublime.Phantom(
			region=Region(0, self.view.size()),
			content=tree,
			layout=sublime.LAYOUT_INLINE,
			on_navigate=self._open_chat
		)
		sublime.PhantomSet(self.view, KEY_CONTACTS_PHANTOM_SET).update([phantom, phantom])

	def _open_chat(self, chat_thread_id):
		self.view.window().run_command(
			COMMAND_OPEN_CHAT,
			{"chat_thread_id": chat_thread_id}
		)
		return


class OpenChatCommand(sublime_plugin.WindowCommand):

	def __init__(self, window):
		super().__init__(window)

	def run(self, chat_thread_id):
		if hasattr(self, 'toggled') and self.toggled:
			return self._close_chat()
		self._open_chat(chat_thread_id)

	def _open_chat(self, chat_thread_id):
		self.window.run_command('set_layout', {
			"cols": [0, 0.70, 1.0],
			"rows": [0.0, 1.0],
			"cells": [[0, 0, 1, 1], [1, 0, 2, 1]]
		})
		self.toggled = True

		self.chat = ChatView()
		self.chat.view = sublime.active_window().new_file()
		self.chat.id = chat_thread_id
		manager.set_chat(self.chat)

		self.chat.view.set_name(self.chat.name)
		self.chat.view.run_command(
			COMMAND_INSERT_CHAT_MESSAGES,
			{"messages": [str(m) for m in quip.get_messages(chat_thread_id)]}
		)

	def _close_chat(self):
		self.window.run_command('set_layout', {
			"cols": [0, 1.0],
			"rows": [0.0, 1.0],
			"cells": [[0, 0, 1, 1]]
		})
		self.toggled = False
		self.window.focus_view(self.chat.view)
		if self.window.active_view() == self.chat.view:
			self.window.run_command('close')
		manager.reset_chat()


class InsertChatMessagesCommand(sublime_plugin.TextCommand):

	def run(self, edit, messages):
		self.view.erase_phantoms(KEY_MESSAGES_PHANTOM_SET)

		result = ""
		for m in messages:
			result += self._convert_to_html(m)
		manager.chat.view.set_scratch(False)
		manager.chat.view.set_read_only(False)

		phantom = sublime.Phantom(
			region=Region(0, self.view.size()),
			content=result,
			layout=sublime.LAYOUT_BLOCK
		)
		manager.chat.add_phantom(phantom)
		manager.chat.add_phantom(phantom)
		sublime.PhantomSet(self.view, KEY_MESSAGES_PHANTOM_SET).update(manager.chat.phantoms)

		manager.chat.view.set_read_only(True)
		manager.chat.view.set_scratch(True)

	def _convert_to_html(self, message):
		return "<div>%s</div>" % message


class SendChatMessageCommand(sublime_plugin.TextCommand):

	def run(self, edit):
		current_window = sublime.active_window()
		if manager.chat.view:
			current_window.show_input_panel('Enter chat message:', '', self._send_message, None, None)

	def _send_message(self, text: str):
		message = quip.send_message(manager.chat.id, text)
		manager.chat.view.run_command(COMMAND_INSERT_CHAT_MESSAGES, {"messages": [str(message)]})


class UploadChangesOnSave(sublime_plugin.EventListener):

	def on_pre_save(self, view):
		if not manager.contains(view):
			return
		line = view.substr(view.full_line(view.sel()[0]))
		if line.startswith('<') and line.endswith('>\n'):
			html = line
		else:
			html = "<p>" + line + "</p>"

		quip.edit_document(thread_id=manager.get_thread(view), content=html)

	def on_pre_close(self, view):
		manager.remove_tab(view=view)


# Section with test commands!
