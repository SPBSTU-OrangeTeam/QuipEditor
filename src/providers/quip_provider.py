import sublime
from ..deps.quip import QuipClient


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
