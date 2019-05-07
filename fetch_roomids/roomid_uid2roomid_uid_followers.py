"""save_all 查找roomid_uid开头的toml文件
save_one 对每个文件分批次运行，10一个批次，全部运行后，保存toml
输出文件为[[roomid, uid, follower_num], [roomid, uid, follower_num] ...]
"""
import asyncio
import re
import sys
import os

import toml

from bili_web import WebHub
from bili_global import DIRECTORY_ROOMID_UID, DIRECTORY_ROOMID_UID_FOLLOWERS
            
                        
async def save_one(file_url, chuncks_roomid):
    webhub = WebHub()
    list_rooms = []
    for i, piece in enumerate(chuncks_roomid):
        await asyncio.sleep(0.3)
        tasklist = []
        for _, uid in piece:
            task = asyncio.ensure_future(webhub.fetch_follow_num(uid))
            tasklist.append(task)
        if tasklist:
            results = await asyncio.gather(*tasklist)
            for roomid_uid, follow_num in zip(piece, results):
                if follow_num > 300:
                    list_rooms.append((*roomid_uid, follow_num))
        print(f'当前一共{len(list_rooms)}个房间({file_url}第{i}批次)')

    await webhub.var_session.close()

    print(f'一共{len(list_rooms)}个房间')
    
    dict_title = {'roomid': list_rooms}

    file_name = os.path.basename(file_url)
    match_obj = re.search(r'(^\D+)(\d+-\d+)\((\d+)\)\S*\.toml', file_name)
    _, room_range, orig_len = match_obj.groups()
    with open(
            f'{DIRECTORY_ROOMID_UID_FOLLOWERS}/roomid_uid_followers{room_range}({orig_len})_{len(list_rooms)}.toml',
            'w', encoding="utf-8") as f:
        toml.dump(dict_title, f)
 
                        
async def save_all():
    files = [f'{DIRECTORY_ROOMID_UID}/{f}' for f in os.listdir(DIRECTORY_ROOMID_UID)
             if os.path.isfile(f'{DIRECTORY_ROOMID_UID}/{f}')]
    file_urls = []
    for f in files:
        file_name = os.path.basename(f)
        if file_name.endswith(').toml') and file_name.startswith('roomid'):
            print(f'找到文件{f}')
            file_urls.append(f)
    print(f'共计{len(file_urls)}个文件')
    for file_url in file_urls:
        with open(file_url, encoding="utf-8") as f:
            dic_roomid = toml.load(f)
        roomids = dic_roomid['roomid']

        list_tuple_roomid_uid = roomids
        if not list_tuple_roomid_uid:
            continue
        len_list_tuple_roomid_uid = len(list_tuple_roomid_uid)
        print('检查tuple数据', file_url, len_list_tuple_roomid_uid)
        chuncks = [list_tuple_roomid_uid[x: x+10] for x in range(0, len_list_tuple_roomid_uid, 10)]
        last_piece = chuncks[-1]
        print(f'一共{len_list_tuple_roomid_uid}数据,分片情况为{len(chuncks)}份，最后一份为{len(last_piece)}')
        assert not len_list_tuple_roomid_uid - (len(chuncks) - 1) * 10 - len(last_piece)
        await save_one(file_url, chuncks)
    

if sys.platform == 'win32':
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
else:
    loop = asyncio.get_event_loop()

tasks = [
    save_all()
]


loop.run_until_complete(asyncio.wait(tasks))
