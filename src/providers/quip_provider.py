import sublime
#import websocket
import time
import json
import _thread as thread

from ..deps.quip import QuipClient
from ..quip_entity.message import Message
from ..quip_entity.tree_node import TreeNode
from ..quip_entity.user import User


class QuipProvider:

    def __init__(self):
        self.quip_client = QuipClient(
            access_token=sublime.load_settings("SublimeQuip.sublime-settings").get("quip_token", "NOT_FOUND"),
            base_url="https://platform.quip.com")
        self.heartbeat_interval = sublime.load_settings("SublimeQuip.sublime-settings")\
            .get("quip_heartbeat_interval", 20)

    def get_document_thread_ids(self):
        thread_ids = set()
        chunk = list(self.quip_client.get_recent_threads(
            max_updated_usec=None, count=1000).values())
        thread_ids.update([t["thread"]["id"] for t in chunk if t["thread"]["type"] == "document"])
        return thread_ids

    def get_document_content(self, thread_id):
        return self.quip_client.get_thread(thread_id)["html"]

    def create_document(self, document_name, content, content_type="html"):
        return self.quip_client.new_document(content, content_type, document_name)

    def edit_document(self, thread_id, content, content_type="html",
                      operation=QuipClient.APPEND, section_id=None):
        return self.quip_client.edit_document(thread_id, content, operation, content_type, section_id)

    def current_user(self):
        return self.quip_client.get_authenticated_user()

    def get_recent_chats(self):
        threads = self.quip_client.get_recent_threads()
        return [
            (id, threads[id]['thread']['title'])
            for id in threads.keys()
            if threads[id]['thread']['thread_class'] == 'channel' or \
               threads[id]['thread']['thread_class'] == 'two_person_chat'
        ]

    def delete_document(self, thread_id):
        return self.quip_client.delete_thread(thread_id)

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
            for (k, f) in folders.items():
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
        for (k, f) in folders.items():
            children.append(self.__add_folder(f))
        root = TreeNode("root", "root", None, children)
        self.__fill_threads_info(root)
        return root

    def get_contacts(self):
        contacts = self.quip_client.get_contacts()
        user, friend_list = None, list()
        for contact in contacts:
            if contact["affinity"] > 0.0:
                friend_list.append(User(contact["id"], contact["name"], contact["chat_thread_id"],
                                        profile_picture_url=contact["profile_picture_url"]))
            else:
                user = User(contact["id"], contact["name"], None, profile_picture_url=contact["profile_picture_url"])
        return user, friend_list

    def get_comments(self, thread_id):
        messages = self.quip_client.get_messages(thread_id)
        comments = [comment for comment in messages
                    if comment.get('annotation') and comment.get('visible')]
        return comments

    def get_messages(self, thread_id):
        messages = self.quip_client.get_messages(thread_id, count=100)
        # For future if we get a troubles with order of messages
        # sorted(messages, key=lambda message: message["created_usec"], reverse=True)
        chat = [Message(message["text"], message["author_id"], message["author_name"],
                        message["created_usec"], message["updated_usec"])
                for message in messages
                if message["visible"]
                ]
        chat.reverse()
        return chat

    def send_message(self, thread_id, text):
        response = self.quip_client.new_message(thread_id, text)
        return Message(response["text"], response["author_id"], response["author_name"],
                       response["created_usec"], response["updated_usec"]) \
            if response["visible"] else None

    def __on_open(self, ws):
        print("### connection established ###")

        def run(*args):
            while True:
                time.sleep(self.heartbeat_interval)
                ws.send(json.dumps({"type": "heartbeat"}))

        thread.start_new_thread(run, ())

    def subscribe_messages(self, on_message, on_close, on_error):
        websocket_info = self.quip_client.new_websocket()

        ws = websocket.WebSocketApp(
            websocket_info["url"], on_message=on_message, on_error=on_error, on_close=on_close)
        ws.on_open = self.__on_open(ws)
        ws.run_forever()
