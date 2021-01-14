import re
import time

import sublime
import sublime_plugin
import os
from sublime import Region

from .src.editor import HTMLEditor
from .src.providers import QuipProvider
from .src.managers import TREE_VIEW_TAB_ID, TabsManager, ChatView, Preview
from .src.deps.markdownify import markdownify as md


COMMAND_OPEN_DOCUMENT = "open_document"
COMMAND_OPEN_CHAT = "open_chat"
COMMAND_OPEN_PREVIEW = "open_preview"
COMMAND_SHOW_FILE_TREE = "show_file_tree"
COMMAND_PRINT_QUIP_FILE_TREE = "print_quip_file_tree"
COMMAND_INSERT_SELECTED_DOCUMENT = "insert_selected_document"
COMMAND_INSERT_CHAT_MESSAGES = "insert_chat_messages"
COMMAND_INSERT_CONTACTS = "insert_contacts"
COMMAND_INSERT_PREVIEW = "insert_preview"
COMMAND_DELETE_DOCUMENT = "delete_document"
KEY_THREAD_ID = "thread_id"
KEY_FILE_TREE_PHANTOM_SET = "file_tree_phantom_set"
KEY_CONTACTS_PHANTOM_SET = "contacts_phantom_set"
KEY_MESSAGES_PHANTOM_SET = "messages_phantom_set"
KEY_PREVIEW_PHANTOM_SET = "preview_phantom_set"


def plugin_loaded():
	global quip, manager, CACHE_DIRECTORY
	quip = QuipProvider()
	manager = TabsManager()
	CACHE_DIRECTORY = sublime.cache_path() + "/QuipEditor"
	if not os.path.exists(CACHE_DIRECTORY):
		os.makedirs(CACHE_DIRECTORY)


class OpenDocumentCommand(sublime_plugin.WindowCommand):

	def run(self, thread_id, markdown=False, chat=True):	
		self.window.run_command("set_layout", {
			"cols": [0, 1.0],
			"rows": [0.0, 1.0],
			"cells": [[0, 0, 1, 1]]
		})
		view = manager.get_tab(thread_id)
		if not view:
			view = self.window.new_file()
		manager.event_propagation = False
		view.retarget(CACHE_DIRECTORY + "/" + thread_id + ".html")
		view.run_command(COMMAND_INSERT_SELECTED_DOCUMENT, {"thread_id": thread_id, "markdown": markdown, "chat": chat})
		view.run_command("save")
		manager.add(thread_id, view)


class ShowFileTreeCommand(sublime_plugin.WindowCommand):

	def run(self):
		view = manager.get_tab(TREE_VIEW_TAB_ID)
		if not view:
			view = self.window.new_file()
			manager.add(TREE_VIEW_TAB_ID, view)
		self.window.focus_view(view)
		view.run_command(COMMAND_PRINT_QUIP_FILE_TREE)


class InsertSelectedDocumentCommand(sublime_plugin.TextCommand):

	def run(self, edit, thread_id, markdown=False, chat=True):
		html = quip.get_document_content(thread_id)
		self.view.replace(edit, Region(0, self.view.size()), md(html) if markdown else html)
		manager.reset_debounced(thread_id)
		if chat:
			manager.comments[thread_id] = quip.get_comments(thread_id)
			self.view.window().run_command(
				COMMAND_OPEN_CHAT,
				{"thread": thread_id,
				 "name": "Comments",
				 "is_document": True}
			)
			self.view.window().run_command(
				COMMAND_OPEN_PREVIEW,
				{"content": html}
			)
		else:
			manager.preview.view.run_command(
				COMMAND_INSERT_PREVIEW,
				{"content": html}
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
			on_navigate=self._on_click_doc_link
		)
		sublime.PhantomSet(self.view, KEY_FILE_TREE_PHANTOM_SET) \
			.update([phantom, phantom])  # TODO разобраться почему только так работает

	def _on_click_doc_link(self, command):
		args = command.split(":")
		if len(args) == 2:
			if args[0] == "open":
				self.view.window().run_command(COMMAND_OPEN_DOCUMENT, {"thread_id": args[1], "markdown": False})
			if args[0] == "delete":
				self.view.window().run_command(COMMAND_DELETE_DOCUMENT, {"thread_id": args[1]})


	def _print_tree(self, node, prefix, postfix):
		if node is None:
			return ""
		thread_name = node.name
		if node.thread_type == "document":
			thread_name = "<a href=\"open:{0}\">{1}</a>".format(node.thread_id, node.name)
			str_result = "{0} Name: {1} | Type: {2}{3} (<a href=\"delete:{4}\">Delete</a>)".format(
				prefix,
				thread_name,
				node.thread_type,
				postfix,
				node.thread_id
			)
		else:
			str_result = "{0} Name: {1} | Type: {2}{3}".format(
				prefix,
				thread_name,
				node.thread_type,
				postfix,
				node.thread_id
			)
		if node.children is None:
			return str_result
		for child in node.children:
			str_result += "<ul>" + self._print_tree(child, "<li>", "</li>") + "</ul>"
		return str_result


class DeleteDocumentCommand(sublime_plugin.TextCommand):

	def run(self, edit, thread_id, markdown=False, chat=False):
		isOk = sublime.ok_cancel_dialog("Удалить документ?", "Удалить")
		if isOk:
			response = quip.delete_document(thread_id)
			if len(response) == 0:
				self.view.window().run_command(COMMAND_SHOW_FILE_TREE)


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
		tree += "\n".join(["<li>%s</li>" % str(friend) for friend in friends if friend])
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

	def run(self, thread=None, name="Private Chat", is_document=False):
		self.window.run_command("close_chat")
		self._open_chat(thread, name, is_document)

	def _open_chat(self, thread, name, is_document):
		if not thread:
			return
		self.window.run_command("set_layout", {
			"cols": [0, 0.6, 1.0],
			"rows": [0.0, 1.0],
			"cells": [[0, 0, 1, 1], [1, 0, 2, 1]]
		})
		manager.set_chat(
			ChatView(thread, sublime.active_window().new_file(), name, is_document)
		)
		manager.chat.view.run_command(
			COMMAND_INSERT_CHAT_MESSAGES,
			{"messages": [str(m) for m in quip.get_messages(thread)]}
		)

class OpenPreviewCommand(sublime_plugin.WindowCommand):

	def run(self, content, name="Document Preview"): 
		self.window.run_command("close_preview")
		self._open_preview(content, name)

	def _open_preview(self, content, name):
		manager.set_preview(
			Preview(content, sublime.active_window().new_file(), name)
		)
		manager.preview.view.run_command(
			COMMAND_INSERT_PREVIEW,
			{"content": content}
		)


class InsertPreviewCommand(sublime_plugin.TextCommand):

	def run(self, edit, content):
		self.view.erase_phantoms(KEY_PREVIEW_PHANTOM_SET)

		manager.preview.view.set_scratch(False)
		manager.preview.view.set_read_only(False)

		phantom = sublime.Phantom(
			region=Region(0, self.view.size()),
			content=content.replace("<br/>", ""),
			layout=sublime.LAYOUT_INLINE
		)
		manager.preview.phantom = [phantom, phantom]
		sublime.PhantomSet(self.view, KEY_PREVIEW_PHANTOM_SET).update(manager.preview.phantom)

		manager.preview.view.set_read_only(True)
		manager.preview.view.set_scratch(True)

class CloseChatCommand(sublime_plugin.WindowCommand):

	def run(self):
		if not manager.chat or not manager.chat.view:
			return
		manager.chat.view.close()
		manager.reset_chat() 
		if manager.preview and manager.preview.view:
			return			
		self.window.run_command("set_layout", {
			"cols": [0, 1.0],
			"rows": [0.0, 1.0],
			"cells": [[0, 0, 1, 1]]
		})

class ClosePreviewCommand(sublime_plugin.WindowCommand):

	def run(self):
		if not manager.preview or not manager.preview.view:		
			return

		manager.preview.view.close()
		manager.reset_preview()
		if not manager.chat or not manager.chat.view:			
			self.window.run_command("set_layout", {
				"cols": [0, 1.0],
				"rows": [0.0, 1.0],
				"cells": [[0, 0, 1, 1]]
			})


class InsertChatMessagesCommand(sublime_plugin.TextCommand):

	def run(self, edit, messages):
		self.view.erase_phantoms(KEY_MESSAGES_PHANTOM_SET)

		result = "".join([self._convert_to_html(m) for m in messages])
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
			current_window.show_input_panel("Enter chat message:", "", self._send_message, None, None)

	def _send_message(self, text: str):
		if not manager.chat or not manager.chat.id:
			return
		message = quip.send_message(manager.chat.id, text)
		manager.chat.view.run_command(COMMAND_INSERT_CHAT_MESSAGES, {"messages": [str(message)]})


class UploadChangesOnSave(sublime_plugin.EventListener):

	def on_pre_save(self, view):
		if not manager.contains(view) or not manager.event_propagation:
			return
		editor = HTMLEditor(view)
		thread = manager.get_thread(view)

		for line, section in editor.edited:
			quip.edit_document(
				thread_id=thread, content=line,
				operation=4, section_id=section
			)
		for line, section in editor.new:
			quip.edit_document(
				thread_id=thread, content=line,
				operation=2 if section else 0,
				section_id=section, content_type="markdown"
			)
		for line, section in editor.deleted:
			quip.edit_document(
				thread_id=thread, content=line,
				operation=5, section_id=section
			)

		view.run_command(COMMAND_INSERT_SELECTED_DOCUMENT, {"thread_id": thread, "chat": False})
		manager.add(thread, view)

	def on_post_save(self, view):
		sublime.active_window().focus_view(view)
		view.sel().clear()
		manager.event_propagation = True

	def on_close(self, view):
		if manager.chat:
			if manager.chat.view == view:
				sublime.active_window().run_command("close_chat")

			if (manager.get_thread(view) and manager.chat.is_document):
				sublime.active_window().run_command("close_chat")
				sublime.active_window().run_command("close_preview")

		manager.remove_tab(view=view)

	def on_activated(self, view):
		thread = manager.get_thread(view)
		if thread is None or thread == TREE_VIEW_TAB_ID:
			return
		if manager.update_debounced(thread):
			view.run_command(COMMAND_INSERT_SELECTED_DOCUMENT, {"thread_id": thread, "chat": False})
			manager.event_propagation = False
			view.run_command("save")

	# def on_activated_async(self, view):
	# 	thread = manager.get_thread(view)
	# 	if thread is None or thread == TREE_VIEW_TAB_ID or not manager.event_propagation:
	# 		return
	# 	manager.comments[thread] = quip.get_comments(thread)
	# 	view.window().run_command(
	# 		COMMAND_OPEN_CHAT,
	# 		{"thread": thread,
	# 		 "name": "Comments",
	# 		 "is_document": True}
	# 	)
	# 	view.window().run_command(
	# 		COMMAND_OPEN_PREVIEW,
	# 		{"content": view.substr(sublime.Region(0, view.size()))}
	# 	)

	# def on_deactivated_async(self, view):		
	# 	thread = manager.get_thread(view)
	# 	if thread is None or thread == TREE_VIEW_TAB_ID or not manager.event_propagation:
	# 		return
	# 	# manager.chat.view.close()
	# 	# manager.preview.view.close()
	# 	view.window().run_command("set_layout", {
	# 		"cols": [0, 1.0],
	# 		"rows": [0.0, 1.0],
	# 		"cells": [[0, 0, 1, 1]]
	# 	})

class ShowCommentsOnHover(sublime_plugin.EventListener):

	def on_hover(self, view, point, hover_zone):
		thread = manager.get_thread(view)
		messages = manager.comments.get(thread)
		if not messages or view.is_popup_visible():
			return
		word_region = view.word(point)
		word = view.substr(word_region)
		comments = ["<div>" + str(comment) + "</div>" for comment in messages if word in comment.sections]
		view.show_popup("\n".join(comments), flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY, location=point, max_width=600, max_height=1500)
