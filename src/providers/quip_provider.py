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

    def __add_folder(self, folder_id):
        folder = self.quip_client.get_folder(folder_id)
        folders = list()
        children = list()
        for f in folder["children"]:
            if "folder_id" in f:
                children.append(self.__add_folder(f["folder_id"]))
            if "thread_id" in f:                
                thread_info = self.quip_client.get_thread(f["thread_id"])["thread"]
                children.append(TreeNode(thread_info["title"], thread_info["type"], thread_info["id"]))
        folder_root = TreeNode(folder["folder"]["title"], "folder", folder["folder"]["id"], children)
        return folder_root

    def get_thread_tree(self):        
        user = self.quip_client.get_authenticated_user()
        children = list()
        children.append(self.__add_folder(user["private_folder_id"]))
        for folder in user["group_folder_ids"]:
            children.append(self.__add_folder(folder))
        return TreeNode("root", "root", None, children)
