'''
save_all 查找readable开头的toml文件
save_one 对每个readable文件分批次运行，400一个批次，全部运行后，保存toml
输出文件为[(roomid, follower_num), (roomid, follower_num) ...], 过滤了粉丝少于1000的主播
v0.9.6+ toml会输出为[[roomid, follower_num], [roomid, follower_num] ...]
'''
import asyncio
import sys
import toml
import os
from bili_web import WebHub
            
                        
async def save_one(file_url, chuncks_roomid):
    webhub = WebHub()
    list_rooms = []
    for i, piece in enumerate(chuncks_roomid):
        await asyncio.sleep(0.3)
        tasklist = []
        for roomid, uid in piece:
            task = asyncio.ensure_future(webhub.fetch_follow_num(roomid, uid))
            tasklist.append(task)
        if tasklist:
            results = await asyncio.gather(*tasklist)
            for real_roomid, follow_num in results:
                if follow_num > 500:
                    list_rooms.append((real_roomid, follow_num))
        print(f'当前一共{len(list_rooms)}个房间({file_url}第{i}批次)')

    await webhub.var_session.close()

    print(f'一共{len(list_rooms)}个房间')
    
    dict_title = {'roomid': list_rooms}
    
    file_url = file_url.split('.')[0]

    with open(f'roomid_followers{file_url[10:]}_{len(list_rooms)}.toml', 'w', encoding="utf-8") as f:
        toml.dump(dict_title, f)
 
                        
async def save_all():
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    file_urls = []
    for f in files:
        if f[-6:] == ').toml' in f and f[:10] == 'roomid_uid':
            print(f'找到文件{f}')
            file_urls.append(f)
    for file_url in file_urls:
        with open(file_url, encoding="utf-8") as f:
            dic_roomid = toml.load(f)
        roomids = dic_roomid['roomid']
        '''
        num_roomid = len(roomids) / 2
        print('检查string去括号数据', file_url, num_roomid)
        num_roomid = int(num_roomid)
        list_tuple_roomid_uid = []
        for i in range(0, num_roomid):
            roomid = roomids[2 * i]
            uid = roomids[2 * i + 1]
            list_tuple_roomid_uid.append((roomid, uid))
        '''
        list_tuple_roomid_uid = roomids
        len_list_tuple_roomid_uid = len(list_tuple_roomid_uid)
        print('检查tuple数据', file_url, len_list_tuple_roomid_uid)
        chuncks = [list_tuple_roomid_uid[x: x+10] for x in range(0, len_list_tuple_roomid_uid, 10)]
        last_piece = chuncks[-1]
        print(f'一共{len_list_tuple_roomid_uid}数据,分片情况为{len(chuncks)}份，最后一份为{len(last_piece)}')
        print(f'数据校验位为{len_list_tuple_roomid_uid - (len(chuncks) - 1) * 400 - len(last_piece)}')
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
