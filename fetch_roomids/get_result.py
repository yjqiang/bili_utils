import os

import toml

from bili_global import DIRECTORY_SORTED


files = [f'{DIRECTORY_SORTED}/{f}' for f in os.listdir(DIRECTORY_SORTED)
         if os.path.isfile(f'{DIRECTORY_SORTED}/{f}')]
file_urls = []
for f in files:
    file_name = os.path.basename(f)
    if file_name.endswith('.toml') and file_name.startswith('sorted_'):
        print(f'找到文件{f}')
        file_urls.append(f)
assert len(file_urls) == 1
with open(file_urls[0], encoding="utf-8") as f:
    dic_roomid = toml.load(f)
roomids = dic_roomid['roomid']
roomids = [roomid for roomid, _, _ in roomids]
dict_title = {'roomid': roomids}
with open(f'{DIRECTORY_SORTED}/roomid.toml', 'w', encoding="utf-8") as f:
    toml.dump(dict_title, f)
