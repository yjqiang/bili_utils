"""init_min 寻找当前文件夹内文件，用来初始化min，用于中断后的重启
save_all 确定规模50w一个文件
save_one 50w分批次运行，全部运行50w后(过滤短号；过滤不开播的直播间，根据排行榜过滤)，保存toml
输出文件为[[roomid, uid], [roomid, uid] ...]
"""
import asyncio
import sys
import os
import re

import toml

from bili_web import WebHub
from bili_global import DIRECTORY_ROOMID_UID, LEN_CHUNCK, SLEEP


async def save_one(chuncks):
    webhub = WebHub()
    list_rooms = []
    for i, piece in enumerate(chuncks):
        await asyncio.sleep(SLEEP)
        tasks = []
        for roomid in piece:
            task = asyncio.create_task(webhub.fetch_room_info(roomid))
            tasks.append(task)
        results = await asyncio.gather(*tasks)
        list_roomid_uid = [(room_id, uid) for room_id, uid in zip(piece, results) if uid is not None]

        tasks = []
        for roomid, uid in list_roomid_uid:
            task = asyncio.create_task(webhub.fetch_fan_gifts(roomid))
            tasks.append(task)
        if tasks:
            results = await asyncio.gather(*tasks)
            for roomid_uid, num in zip(list_roomid_uid, results):
                if num >= 5:
                    list_rooms.append(roomid_uid)
        print(f'当前一共{len(list_rooms)}个房间({piece[0]}-{piece[-1]})')

    await webhub.var_session.close()

    print(f'一共{len(list_rooms)}个房间')
    
    dict_title = {'roomid': list_rooms}

    with open(
            f'{DIRECTORY_ROOMID_UID}/roomid_uid{chuncks[0][0]}-{chuncks[-1][-1]}({len(list_rooms)}).toml',
            'w', encoding="utf-8") as f:
        toml.dump(dict_title, f)
 
               
def init_min(min_room, max_room, step):
    files = [f'{DIRECTORY_ROOMID_UID}/{f}' for f in os.listdir(DIRECTORY_ROOMID_UID)
             if os.path.isfile(f'{DIRECTORY_ROOMID_UID}/{f}')]
    finished_range_mins = []
    for f in files:
        file_name = os.path.basename(f)
        if file_name.endswith(').toml') and file_name.startswith('roomid_uid'):
            print(f'找到文件{file_name}')
            match_obj = re.search(r'(^\D+)(\d+-\d+)\((\d+)\)\S*\.toml', file_name)
            _, room_range, _ = match_obj.groups()
            finished_range_mins.append(int(room_range.split('-')[0]))
    for i in range(min_room, max_room, step):
        if i not in finished_range_mins:
            print('初始化', i)
            return i
    return None
        

async def save_all():
    min_room = 0
    max_room = 22500000
    step = 500000
    # 收录从min到(max_room-1),min max必须被500000整除
    min_room = init_min(min_room, max_room, step)
    if min_room is None:
        return
    for i in range(min_room, max_room, step):
        list_input = [j for j in range(i, i + step)]
        len_list_input = len(list_input)
        chuncks = [list_input[k: k+LEN_CHUNCK] for k in range(0, step, LEN_CHUNCK)]
        last_piece = chuncks[-1]
        print(f'一共{len_list_input}数据,分片情况为{len(chuncks)}份，最后一份为{len(last_piece)}')
        assert not len_list_input - (len(chuncks) - 1) * LEN_CHUNCK - len(last_piece)
        await save_one(chuncks)

if sys.platform == 'win32':
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)

loop = asyncio.get_event_loop()
loop.run_until_complete(save_all())
