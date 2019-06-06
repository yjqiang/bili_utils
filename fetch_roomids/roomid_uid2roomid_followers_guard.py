"""save_all 查找roomid_uid开头的toml文件
save_one 对每个文件分批次运行，全部运行后，保存toml
输出文件为[[roomid, follower_num, guard_num], [roomid, follower_num, guard_num] ...]
"""
import asyncio
import re
import sys
import os

import toml

from bili_web import WebHub
from bili_global import DIRECTORY_ROOMID_UID, DIRECTORY_ROOMID_FOLLOWERS_GUARD, LEN_CHUNCK, SLEEP


async def save_one(file_name, chuncks):
    webhub = WebHub()
    list_rooms = []
    for i, piece in enumerate(chuncks):
        await asyncio.sleep(SLEEP)
        tasks = []
        for _, uid in piece:
            task = asyncio.create_task(webhub.fetch_follow_num(uid=uid))
            tasks.append(task)
        results0 = await asyncio.gather(*tasks)

        tasks = []
        for _, uid in piece:
            task = asyncio.create_task(webhub.fetch_guard_num(uid=uid))
            tasks.append(task)
        results1 = await asyncio.gather(*tasks)

        for roomid_uid, follow_num, guard_num in zip(piece, results0, results1):
            roomid, _ = roomid_uid
            if follow_num >= 300 or guard_num > 0:
                list_rooms.append((roomid, follow_num, guard_num))
        print(f'当前一共{len(list_rooms)}个房间({file_name}第{i}批次)')

    await webhub.var_session.close()

    print(f'一共{len(list_rooms)}个房间')

    dict_title = {'roomid': list_rooms}

    match_obj = re.search(r'(^\D+)(\d+-\d+)\((\d+)\)\S*\.toml', file_name)
    _, room_range, orig_len = match_obj.groups()
    with open(
            f'{DIRECTORY_ROOMID_FOLLOWERS_GUARD}/roomid_uid_followers{room_range}({orig_len})_{len(list_rooms)}.toml',
            'w', encoding="utf-8") as f:
        toml.dump(dict_title, f)


async def save_all():
    files = [f'{DIRECTORY_ROOMID_UID}/{f}' for f in os.listdir(DIRECTORY_ROOMID_UID)
             if os.path.isfile(f'{DIRECTORY_ROOMID_UID}/{f}')]
    file_urls = []
    for f in files:
        file_name = os.path.basename(f)
        if file_name.endswith(').toml') and file_name.startswith('roomid_uid'):
            print(f'找到文件{f}')
            file_urls.append(f)
    print(f'共计{len(file_urls)}个文件')
    for file_url in file_urls:
        with open(file_url, encoding="utf-8") as f:
            dic_roomid = toml.load(f)
        roomids = dic_roomid['roomid']

        list_input = roomids
        if not list_input:
            continue
        len_list_input = len(list_input)
        print('检查tuple数据', file_url, len_list_input)
        chuncks = [list_input[k: k + LEN_CHUNCK] for k in range(0, len_list_input, LEN_CHUNCK)]
        last_piece = chuncks[-1]
        print(f'一共{len_list_input}数据,分片情况为{len(chuncks)}份，最后一份为{len(last_piece)}')
        assert not len_list_input - (len(chuncks) - 1) * LEN_CHUNCK - len(last_piece)
        await save_one(os.path.basename(file_url), chuncks)


if sys.platform == 'win32':
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)

loop = asyncio.get_event_loop()
loop.run_until_complete(save_all())
