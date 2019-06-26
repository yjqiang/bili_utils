import rsa
import base64
from time import time
from datetime import datetime

import toml


def curr_time():
    return int(time())


def timestamp():
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return time_now


def sign(msg: str, privkey: rsa.PrivateKey) -> str:
    bytes_msg = msg.encode('utf8')
    bytes_signature = rsa.sign(bytes_msg, privkey, 'SHA-256')
    str_signature = base64.b64encode(bytes_signature).decode('utf8')
    return str_signature


# need_name是False, 返回不带name的结果
def make_signature(name: str, privkey: rsa.PrivateKey, need_name=True) -> dict:
    int_curr_time = curr_time()
    msg = f'Hello World. This is {name} at {int_curr_time}.'
    str_signature = sign(msg, privkey)
    if need_name:
        return {
            'signature': str_signature,
            'time': int_curr_time,
            'name': name
        }
    return {
        'signature': str_signature,
        'time': int_curr_time
    }


def read_toml(file_path):
    with open(file_path, encoding="utf-8") as f:
        return toml.load(f)
