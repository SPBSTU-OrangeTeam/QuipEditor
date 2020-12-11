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
        self.edited = updated_usec - created_usec >= 1_000_000
        self.timestamp = datetime.fromtimestamp(max(updated_usec, created_usec)/(1_000_000))

    def __str__(self):
        return "%s | %s [%s] %s: %s" % (self.author_id, self.author_name, 
                self.timestamp, "(edited)" if self.edited else "", self.text)
            
