import sublime
import sublime_plugin
from .src.providers import quip_provider

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
		self.view.insert(edit, 0, quipprovider.get_document_content(thread_ids.pop()))

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
		print(file_tree)
		print(string_tree)
		self.view.insert(edit, 0, string_tree)