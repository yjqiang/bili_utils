'''
过滤不开播的直播间，根据排行榜过滤
'''
import toml
import asyncio
import sys
from bili_web import WebHub


async def save_one(chuncks_roomid):
    webhub = WebHub()
    list_rooms = []
    for i, piece in enumerate(chuncks_roomid):
        await asyncio.sleep(0.1)
        tasklist = []
        for roomid in piece:
            task = asyncio.ensure_future(webhub.fetch_fan_gifts(roomid))
            tasklist.append(task)
        if tasklist:
            results = await asyncio.gather(*tasklist)
            for num, roomid in results:
                if num >= 9:
                    list_rooms.append(roomid)
        print(f'当前一共{len(list_rooms)}个房间(第{i}批次)')

    await webhub.var_session.close()

    print(f'一共{len(list_rooms)}个房间')
    
    dict_title = {'roomid': list_rooms}

    with open(f'new_{len(list_rooms)}.toml', 'w', encoding="utf-8") as f:
        toml.dump(dict_title, f)

async def func():
    with open('roomid.toml', encoding="utf-8") as f:
        dic_user = toml.load(f)
    
        unique_list = []
        for i in dic_user['roomid']:
            if i not in unique_list:
                unique_list.append(i)
            if len(unique_list) == 6000:
                break
        print(f'总获取房间{len(unique_list)}')
    len_unique_list = len(unique_list)
    chuncks = [unique_list[x: x+400] for x in range(0, len_unique_list, 400)]
    last_piece = chuncks[-1]
    print(f'一共{len_unique_list}数据,分片情况为{len(chuncks)}份，最后一份为{len(last_piece)}')
    print(f'数据校验位为{len_unique_list - (len(chuncks) - 1) * 400 - len(last_piece)}')
    await save_one(chuncks)
    
if sys.platform == 'win32':
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
else:
    loop = asyncio.get_event_loop()

tasks = [
    func()
]


loop.run_until_complete(asyncio.wait(tasks))
