from sublime import *
from sublime_plugin import *

FILE_TREE_TAB_ID = "file_tree_tab_id"

class TabsManager:

    def __init__(self):
        self.visible_tabs = dict()

    def add_tab(self, thread_id, view):
        self.visible_tabs[thread_id] = view

    def remove_tab(self, thread_id):
        del self.visible_tabs[thread_id]

    def remove_tab_by_view(self, view):
        delete_key = None
        print("try del")
        for k in self.visible_tabs.keys():
            if self.visible_tabs[k] == view:
                delete_key = k
                print("find")
                break
        if delete_key is not None:
            del self.visible_tabs[delete_key]
            print("deleted")

    def get_tab(self, thread_id):
        assert self.contains_tab(thread_id)
        return self.visible_tabs[thread_id]

    def contains_tab(self, thread_id):
        return True if thread_id in self.visible_tabs.keys() else False
