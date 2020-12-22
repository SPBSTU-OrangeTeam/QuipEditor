import sublime
import sublime_plugin
import os
from sublime import Region
from .src.providers import QuipProvider
from .src.managers import TREE_VIEW_TAB_ID, TabsManager, ChatView
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

	def run(self, thread_id, markdown=True):
		view = manager.get_tab(thread_id)
		if not view:
			view = self.window.new_file()
		self.window.focus_view(view)
		view.retarget(CACHE_DIRECTORY + "/" + thread_id + ".html")
		view.run_command(COMMAND_INSERT_SELECTED_DOCUMENT, {"thread_id": thread_id, 'markdown': markdown})
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

	def run(self, edit, thread_id, markdown):
		html = quip.get_document_content(thread_id)
		self.view.replace(edit, Region(0, self.view.size()), html) #md(html) if markdown else html)
		manager.comments[thread_id] = quip.get_comments(thread_id)
		self.view.window().run_command(
			COMMAND_OPEN_CHAT,
			{"thread": thread_id,
			 'name': 'Comments'}
		)


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
		tree = str(user) if friends else "Нет контактов"
		tree += "<ul>"
		tree += '\n'.join(["<li>%s</li>" % str(friend) for friend in friends if friend])
		tree += "</ul>"

		phantom = sublime.Phantom(
			region=Region(0, self.view.size()),
			content=tree,
			layout=sublime.LAYOUT_INLINE,
			on_navigate=lambda thread: self.view.window().run_command(
				COMMAND_OPEN_CHAT,
				{"thread": thread}
			)
		)
		sublime.PhantomSet(self.view, KEY_CONTACTS_PHANTOM_SET).update([phantom, phantom])


class OpenChatCommand(sublime_plugin.WindowCommand):

	def __init__(self, window):
		super().__init__(window)

	def run(self, thread=None, name='Private Chat'):
		self._close_chat()
		self._open_chat(thread, name)

	def _open_chat(self, thread, name):
		if not thread:
			return
		self.window.run_command('set_layout', {
			"cols": [0, 1.0],
			"rows": [0.0, 1.0],
			"cells": [[0, 0, 1, 1]]
		})
		self.window.run_command('set_layout', {
			"cols": [0, 0.60, 1.0],
			"rows": [0.0, 1.0],
			"cells": [[0, 0, 1, 1], [1, 0, 2, 1]]
		})
		chat = ChatView(thread, sublime.active_window().new_file(), name)
		manager.set_chat(chat)
		manager.chat.view.run_command(
			COMMAND_INSERT_CHAT_MESSAGES,
			{"messages": [str(m) for m in quip.get_messages(thread)]}
		)

	def _close_chat(self):
		if not manager.chat or not manager.chat.view:
			return
		self.window.focus_view(manager.chat.view)
		if self.window.active_view() == manager.chat.view:
			self.window.run_command('close')


class InsertChatMessagesCommand(sublime_plugin.TextCommand):

	def run(self, edit, messages):
		self.view.erase_phantoms(KEY_MESSAGES_PHANTOM_SET)

		result = ''.join([self._convert_to_html(m) for m in messages])
		manager.chat.view.set_scratch(False)
		manager.chat.view.set_read_only(False)

		phantom = sublime.Phantom(
			region=Region(0, self.view.size()),
			content=result,
			layout=sublime.LAYOUT_INLINE
		)
		manager.chat.add_phantom(phantom)
		sublime.PhantomSet(self.view, KEY_MESSAGES_PHANTOM_SET).update(manager.chat.phantoms)

		manager.chat.view.set_read_only(True)
		manager.chat.view.set_scratch(True)

	def _convert_to_html(self, message):
		return "<div>%s</div>" % message


class SendChatMessageCommand(sublime_plugin.TextCommand):

	def run(self, edit):
		current_window = sublime.active_window()
		if manager.chat and manager.chat.view:
			current_window.show_input_panel('Enter chat message:', '', self._send_message, None, None)

	def _send_message(self, text: str):
		if not manager.chat or not manager.chat.id:
			return
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

	def on_close(self, view):
		if manager.chat and manager.chat.view == view:
			sublime.active_window().run_command('set_layout', {
				"cols": [0, 1.0],
				"rows": [0.0, 1.0],
				"cells": [[0, 0, 1, 1]]
			})
			manager.reset_chat()
		manager.remove_tab(view=view)


class ShowCommentsOnHover(sublime_plugin.EventListener):

	def on_hover(self, view, point, hover_zone):
		thread = manager.get_thread(view)
		messages = manager.comments.get(thread)
		if not messages or view.is_popup_visible():
			return
		word_region = view.word(point)
		word = view.substr(word_region)
		comments = [str(comment) for comment in messages if word in comment.sections]
		view.sel().clear()
		view.sel().add(Region(point))
		view.show_popup_menu(comments, None)
		#view.show_popup('\n'.join(comments), flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY, location=point)
