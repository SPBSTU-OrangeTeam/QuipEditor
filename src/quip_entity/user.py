import sublime
import urllib.request
import os


PROFILE_PICTURES_DIRECTORY = "QuipEditor\\resources\\users\\profile_pictures"
if not os.path.exists(os.path.join(sublime.cache_path(), PROFILE_PICTURES_DIRECTORY)):
    os.makedirs(os.path.join(sublime.cache_path(), PROFILE_PICTURES_DIRECTORY))


def load_picture(picture_url, user_id):
    picture_path = "%s\\%s.png" % (PROFILE_PICTURES_DIRECTORY, user_id)
    urllib.request.urlretrieve(picture_url, os.path.join(sublime.cache_path(), picture_path))
    return picture_path


class User:
    def __init__(self, user_id, name, chat_thread_id, profile_picture_url=None, profile_picture_path=None):
        self.id = user_id
        self.name = name
        self.chat_thread_id = chat_thread_id
        self.profile_picture_path = profile_picture_path
        if profile_picture_url is not None:
            self.profile_picture_path = load_picture(profile_picture_url, self.id)
