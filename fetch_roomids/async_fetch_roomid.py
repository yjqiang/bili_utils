'''
init_min 寻找当前文件夹内文件，用来初始化min，用于中断后的重启
save_all 确定规模50w一个文件
save_one 50w分批次运行，400一个批次，全部运行50w后(过滤短号；过滤不开播的直播间，根据排行榜过滤)，保存toml
输出文件为[(roomid, uid), (roomid, uid) ...]
v0.9.6+ toml会输出为[[roomid, uid], [roomid, uid] ...]
'''
import asyncio
import sys
import toml
import os
from bili_web import WebHub


async def save_one(room_min, room_max):
    # 0 400 收录 0-399
    # 400 1200  收录 400-1199
    # room_min, room_max必须被400整除
    webhub = WebHub()
    list_rooms = []
    step = 10
    for i in range(room_min, room_max, step):
        await asyncio.sleep(0.3)
        tasklist0 = []
        list_roomid_uid = []
        for roomid in range(i, i + step):
            task = asyncio.ensure_future(webhub.fetch_room_info(roomid))
            tasklist0.append(task)
        if tasklist0:
            results = await asyncio.gather(*tasklist0)
            list_roomid_uid = [(real_roomid, uid) for real_roomid, uid in results if real_roomid is not None]
        # print(real_roomid)
        tasklist1 = []
        for roomid, uid in list_roomid_uid:
            task = asyncio.ensure_future(webhub.fetch_fan_gifts(roomid, uid))
            tasklist1.append(task)
        if tasklist1:
            results = await asyncio.gather(*tasklist1)
            for num, roomid, uid in results:
                if num >= 8:
                    list_rooms.append((roomid, uid))
        print(f'当前一共{len(list_rooms)}个房间({room_min}-{i+step-1})')

    await webhub.var_session.close()

    print(f'一共{len(list_rooms)}个房间')
    
    dict_title = {'roomid': list_rooms}

    with open(f'roomid_uid{room_min}-{room_max-1}({len(list_rooms)}).toml', 'w', encoding="utf-8") as f:
        toml.dump(dict_title, f)
 
               
def init_min(min_room, max_room, step):
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    finished_range_mins = []
    for f in files:
        if f[-6:] == ').toml':
            print(f'找到文件{f}')
            finished_range_mins.append(int(f.split('-')[0]))
    for i in range(min_room, max_room, step):
        if i not in finished_range_mins:
            print('初始化', i)
            return i
        
async def save_all():
    min_room = 0
    max_room = 16000000
    step = 500000
    # 收录从min到(max_room-1),min max必须被500000整除
    min_room = init_min(min_room, max_room, step)
    
    for i in range(min_room, max_room, step):
        await save_one(i, i + step)

if sys.platform == 'win32':
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
else:
    loop = asyncio.get_event_loop()

tasks = [
    save_all()
]


loop.run_until_complete(asyncio.wait(tasks))
