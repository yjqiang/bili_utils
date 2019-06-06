import os
from operator import itemgetter

import toml

from bili_global import DIRECTORY_ROOMID_FOLLOWERS_GUARD, DIRECTORY_SORTED


def sort_all():
    files = [f'{DIRECTORY_ROOMID_FOLLOWERS_GUARD}/{f}' for f in os.listdir(DIRECTORY_ROOMID_FOLLOWERS_GUARD)
             if os.path.isfile(f'{DIRECTORY_ROOMID_FOLLOWERS_GUARD}/{f}')]
    file_urls = []
    for f in files:
        file_name = os.path.basename(f)
        if file_name.endswith('.toml') and file_name.startswith('roomid'):
            print(f'找到文件{f}')
            file_urls.append(f)
    list_roomid_followers_guard = []
    for file_url in file_urls:
        with open(file_url, encoding="utf-8") as f:
            dic_roomid = toml.load(f)
        roomids = dic_roomid['roomid']
        list_roomid_followers_guard = list_roomid_followers_guard + roomids
    
    print(len(list_roomid_followers_guard))
    new_list_roomid_followers_guard = []
    for roomid, followers, guard in list_roomid_followers_guard:
        if guard <= 1:
            guard = 0
        new_list_roomid_followers_guard.append((roomid, followers, guard))
    list_roomid_followers_guard = new_list_roomid_followers_guard


    list_roomid_followers_guard.sort(key=itemgetter(2, 1), reverse=True)
    print(list_roomid_followers_guard[:50])
    print(list_roomid_followers_guard[-50:])
    
    dict_title = {'roomid': list_roomid_followers_guard}
    with open(f'{DIRECTORY_SORTED}/sorted_{len(list_roomid_followers_guard)}.toml', 'w', encoding="utf-8") as f:
        toml.dump(dict_title, f)


sort_all()
