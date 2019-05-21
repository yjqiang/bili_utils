from time import time
from datetime import datetime


def curr_time():
    return int(time())


def timestamp():
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return time_now
