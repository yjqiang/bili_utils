import toml
import os
from operator import itemgetter


def sort_all():
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    file_urls = []
    for f in files:
        if f[-5:] == '.toml' and f[:16] == 'roomid_followers':
            print(f'找到文件{f}')
            file_urls.append(f)
    list_roomid_follower = []
    for file_url in file_urls:
        with open(file_url, encoding="utf-8") as f:
            dic_roomid = toml.load(f)
        roomids = dic_roomid['roomid']
        '''
        num_roomid = len(roomids) / 2
        print('检查string去括号数据', file_url, num_roomid)
        num_roomid = int(num_roomid)
        for i in range(0, num_roomid):
            roomid = roomids[2 * i]
            follower_num = roomids[2 * i + 1]
            list_roomid_follower.append((roomid, follower_num))
        '''
        list_roomid_follower = list_roomid_follower + roomids
    
    print(len(list_roomid_follower))
    list_roomid_follower.sort(key=itemgetter(1), reverse=True)
    print(list_roomid_follower[:10])
    print(list_roomid_follower[-400:])
    
    dict_title = {'roomid': list_roomid_follower}
    with open(f'sorted_{len(list_roomid_follower)}.toml', 'w', encoding="utf-8") as f:
        toml.dump(dict_title, f)

sort_all()

    

