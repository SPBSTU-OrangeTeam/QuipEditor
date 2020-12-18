TREE_VIEW_TAB_ID = "TREE_VIEW_TAB_ID"


class TabsManager:

    def __init__(self):
        self._tabs = dict()
        self.chat = None
        self.chat_id = None
        self.comments = dict()

    def add(self, thread: int, view):
        self._tabs[thread] = view

    def get_thread(self, view):
        for thread, item in self._tabs.items():
            if item == view:
                return thread
        return None

    def get_tab(self, thread_id):
        return self._tabs.get(thread_id)

    def contains(self, view):
        return view in self._tabs.values()

    def set_chat(self, thread_id, view):
        self.chat = view
        self.chat_id = thread_id

    def reset_chat(self):
        if self.chat_id:
            self.remove_tab(thread=self.chat_id)
        self.chat = None
        self.chat_id = None

    def remove_tab(self, thread=None, view=None):
        """ You must provide one parameter, though both is fine too """
        if not (thread or view):
            return
        if thread:
            self._remove_by_thread(thread)
        if view:
            self._remove_by_view(view)

    def _remove_by_thread(self, thread):
        self._tabs.pop(thread, None)

    def _remove_by_view(self, view):
        keys = [key for key, item in self._tabs.items() if item == view]
        for key in keys:
            self._tabs.pop(key, None)
