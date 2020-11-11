import sublime
from ..deps.quip import QuipClient
from ..quip_tree.tree_node import TreeNode


class QuipProvider:
    def __init__(self):
        self.quip_client = QuipClient(
            access_token=sublime.load_settings("SublimeQuip.sublime-settings").get("quip_token", "NOT_FOUND"),
            base_url="https://platform.quip.com")

    def get_document_thread_ids(self):
        thread_ids = set()
        chunk = list(self.quip_client.get_recent_threads(
            max_updated_usec=None, count=1000).values())
        thread_ids.update([t["thread"]["id"] for t in chunk if t["thread"]["type"] == "document"])
        return thread_ids

    def get_document_content(self, thread_id):
        return self.quip_client.get_thread(thread_id)["html"]

    def create_document(self, document_name, content, content_type = "html"):
        return self.quip_client.new_document(content, content_type, document_name)

    def edit_document(self, thread_id, content, content_type = "html", 
        operation = QuipClient.APPEND, section_id = None):
        return self.quip_client.edit_document(thread_id, content, operation, content_type, section_id)

    def __add_folder(self, folder):
        folder_ids = list()
        children = list()
        for f in folder["children"]:
            if "folder_id" in f:
                folder_ids.append(f["folder_id"])
            if "thread_id" in f:
                children.append(TreeNode(None, "thread", f["thread_id"]))        
        
        if folder_ids:
            folders = self.quip_client.get_folders(folder_ids)
            for (k,f) in folders.items():
                children.append(self.__add_folder(f))

        return TreeNode(folder["folder"]["title"], "folder", folder["folder"]["id"], children)

    def __fill_threads_info(self, root_tree):
        stack = [root_tree]
        thread_node_dict = {}
        while stack:
            current_node = stack.pop()
            if current_node.children:
                stack += current_node.children
            if current_node.thread_type == "thread":
                thread_node_dict[current_node.thread_id] = current_node

        threads = self.quip_client.get_threads(thread_node_dict.keys())
        for key, value in thread_node_dict.items():
            value.thread_type = threads[key]["thread"]["type"]
            value.name = threads[key]["thread"]["title"]

    def get_thread_tree(self):        
        user = self.quip_client.get_authenticated_user()
        children = list()
        folder_ids = [user["private_folder_id"]] + user["group_folder_ids"]
        folders = self.quip_client.get_folders(folder_ids)
        for (k,f) in folders.items():
            children.append(self.__add_folder(f))
        root = TreeNode("root", "root", None, children)
        self.__fill_threads_info(root)
        return root
