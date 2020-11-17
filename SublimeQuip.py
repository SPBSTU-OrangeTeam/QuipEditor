import sublime
import sublime_plugin
from .src.providers import quip_provider
from sublime import View


class CurrentDocument:

	def __init__(self, id: int = 0, name: str = "", thread: int = 0, view: View = None):
		self.id = view.id() if view else id
		self.name = view.name() if view else name
		self.thread = thread

	def check(self, view: View) -> bool:
		return self.id == view.id()
	

current = CurrentDocument()

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
		global current
		current = CurrentDocument(view=self.view, thread=id)
		self.view.insert(edit, 0, quipprovider.get_document_content(id))

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
		global current
		if not current.check(view):
			return

		quip = quip_provider.QuipProvider()
		line = view.substr(view.full_line(view.sel()[0]))
		if line.startswith('<') and line.endswith('>\n'):
			html = line
		else:
			html = "<p>" + line + "</p>"

		if current.thread:
			quip.edit_document(thread_id=current.thread, content=html)




