from datetime import datetime, timedelta
import time


def convert_datetime(timestamp):
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    return timestamp + offset


class Message:
    def __init__(self, text, author_id, author_name, created_usec, updated_usec):
        self.text = text
        self.author_id = author_id
        self.author_name = author_name
        # if difference between created and updated usec more than 1 second
        self.edited = updated_usec - created_usec > 1000000
        microseconds_since_epoch = updated_usec if self.edited else created_usec
        self.timestamp = convert_datetime(datetime(1970, 1, 1) + timedelta(microseconds=microseconds_since_epoch))
