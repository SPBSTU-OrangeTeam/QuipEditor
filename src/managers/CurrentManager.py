from sublime import View

class CurrentManager:

    def __init__(self):
        self._threads = dict()
        self.comments = dict()
        self.reset_chat()

    def add(self, thread: int, view: View = None, view_id: int = 0) -> (int, bool):
        id = view.id() if view else view_id
        if not id:
            return 0, False
        overwrite = self.contains(view_id=id)
        self._threads[id] = thread
        return id, overwrite

    def get(self, view: View = None, view_id: int = 0) -> str:
        id = view.id() if view else view_id
        return self._threads.get(id)

    def contains(self, view: View = None, view_id: int = 0) -> bool:
        return (view.id() if view else view_id) in self._threads.keys()

    def set_chat(self, id: str, view: View):
        self.chat = view
        self.chat_id = id

    def reset_chat(self):
        self.chat = None
        self.chat_id = None


