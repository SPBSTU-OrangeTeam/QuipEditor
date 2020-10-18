from ..deps import quip


class QuipProvider:

    def __init__(self, access_token):
        self.quip_client = quip.QuipClient(
            access_token=access_token,
            base_url="https://platform.quip.com")

    def get_document_thread_ids(self):
        thread_ids = set()
        chunk = list(self.quip_client.get_recent_threads(
            max_updated_usec=None, count=1000).values())
        thread_ids.update([t["thread"]["id"] for t in chunk if t["thread"]["type"] == "document"])
        return thread_ids

    def get_document_content(self, threadId):
        return self.quip_client.get_thread(threadId)["html"]