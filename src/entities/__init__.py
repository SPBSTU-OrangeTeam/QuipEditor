from datetime import datetime
import random

class Message:
    
    def __init__(self, text, author_id, author_name, created_at, updated_at):
        self.text = text
        self.author_id = author_id
        self.author_name = author_name
        
        self.edited = updated_at - created_at >= 10**6  # If difference more than 1 second
        self.timestamp = datetime.fromtimestamp(max(updated_at, created_at)/(10**6))

    def __str__(self):
        return "%s | %s [%s] %s: %s" % (self.author_id, self.author_name, 
                self.timestamp, "(edited)" if self.edited else "", self.text)


class TreeNode:
    
    def __init__(self, name, thread_type, thread_id, children=None):
        self.name = name
        self.thread_type = thread_type
        self.thread_id = thread_id
        self.children = children


class User:

    def __init__(self, user_id, name, chat_thread_id = None):
        self.avatar = random.choice(['😎', '🥺', '😃', '🐻', '🙊'])
        self.id = user_id
        self.name = name
        self.chat_thread_id = chat_thread_id
