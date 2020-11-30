import sublime
import sublime_plugin
from .src.providers import quip_provider
from .CurrentManager import CurrentManager

COMMAND_OPEN_DOCUMENT = "open_recent_document"
COMMAND_PRINT_QUIP_FILE_TREE = "print_quip_file_tree"
COMMAND_GET_SELECTED_DOCUMENT = "insert_selected_document"
COMMAND_GET_RANDOM_DOCUMENT = "insert_random_document_html"

KEY_THREAD_ID = "thread_id"

current = CurrentManager()

class OpenRecentDocumentCommand(sublime_plugin.WindowCommand):
	def run(self, **args):
		view = self.window.new_file()
		thread_id = args[KEY_THREAD_ID]
		if thread_id is not None:
			view.run_command(COMMAND_GET_SELECTED_DOCUMENT, args)
		else:
			view.run_command(COMMAND_GET_RANDOM_DOCUMENT)

class ShowFileTreeCommand(sublime_plugin.WindowCommand):
	def run(self):
		view = self.window.new_file()
		view.run_command(COMMAND_PRINT_QUIP_FILE_TREE)

class InsertRandomDocumentHtmlCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		quipprovider = quip_provider.QuipProvider()
		thread_ids = quipprovider.get_document_thread_ids()
		id = thread_ids.pop()
		current.add(view=self.view, thread=id)
		self.view.insert(edit, 0, quipprovider.get_document_content(id))

class InsertSelectedDocumentCommand(sublime_plugin.TextCommand):
	def run(self, edit, **args):
		quipprovider = quip_provider.QuipProvider()
		doc_id = args[KEY_THREAD_ID]
		assert doc_id is not None
		current.add(view=self.view, thread=doc_id)
		self.view.insert(edit, 0, quipprovider.get_document_content(doc_id))

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
		sublime.PhantomSet(self.view, "file_tree_phantom_set")\
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




