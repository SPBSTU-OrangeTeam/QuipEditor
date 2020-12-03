import sublime
import urllib.request
from os.path import join


def load_picture(picture_url, user_id):
    picture_path = "SublimeQuip/resources/users/profile_pictures/%s.png" % user_id
    urllib.request.urlretrieve(picture_url, join(sublime.packages_path(), picture_path))
    return picture_path


class User:
    def __init__(self, user_id, name, chat_thread_id, profile_picture_url=None, profile_picture_path=None):
        self.id = user_id
        self.name = name
        self.chat_thread_id = chat_thread_id
        self.profile_picture_path = profile_picture_path
        if profile_picture_url is not None:
            self.profile_picture_path = load_picture(profile_picture_url, self.id)
