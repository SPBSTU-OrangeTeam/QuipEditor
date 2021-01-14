from datetime import datetime

TREE_VIEW_TAB_ID = "TREE_VIEW_TAB_ID"


class ChatView:

    def __init__(self, id=None, view=None, name="Private Chat", is_document=False):
        self.id = id
        self.view = view
        self.name = name
        self.is_document = is_document
        self.phantoms = []

        if self.view and self.name:
            self.view.set_name(name)

    def add_phantom(self, phantom):
        self.phantoms.extend([phantom, phantom])


class Preview:

    def __init__(self, content = None, view=None, name="HTML Preview"):
        self.content = content
        self.view = view
        self.name = name
        self.phantoms = []

        if self.view and self.name:
            self.view.set_name(name)

    def add_phantom(self, phantom):
        self.phantoms.extend([phantom, phantom])

class TabsManager:

    def __init__(self):
        self._tabs = dict()
        self.chat = ChatView()
        self.preview = Preview()
        self.comments = dict()
        self._upload_timestamps = dict()
        self.event_propagation = False



    def add(self, thread: int, view):
        self._tabs[thread] = view
        self._upload_timestamps[thread] = datetime.now().microsecond

    def get_thread(self, view):
        for thread, item in self._tabs.items():
            if item == view:
                return thread
        return None

    def get_tab(self, thread_id):
        return self._tabs.get(thread_id)

    def contains(self, view):
        return view in self._tabs.values()

    def set_chat(self, chat):
        self.chat = chat

    def set_preview(self, preview):
        self.preview = preview

    def reset_chat(self):
        if self.chat and self.chat.id:
            self.remove_tab(thread=self.chat.id)
        self.chat = None

    def reset_preview(self):
        self.preview = None

    def remove_tab(self, thread=None, view=None):
        """ You must provide one parameter, though both is fine too """
        if not (thread or view):
            return
        if thread:
            self._remove_by_thread(thread)
        if view:
            self._remove_by_view(view)

    def update_debounced(self, thread: int):
        if self._upload_timestamps[thread] is None:
            return True
        if datetime.now().microsecond - self._upload_timestamps[thread] > 15*1000:
            return True
        return False

    def reset_debounced(self, thread: int):
        self._upload_timestamps[thread] = datetime.now().microsecond


    def _remove_by_thread(self, thread):
        self._tabs.pop(thread, None)

    def _remove_by_view(self, view):
        keys = [key for key, item in self._tabs.items() if item == view]
        for key in keys:
            self._tabs.pop(key, None)
