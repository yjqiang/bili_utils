import asyncio
import aiohttp
import sys
import toml
import json
import os


class WebHub:
    
    def __init__(self):
        self.var_session = None

    @property
    def session(self):
        if self.var_session is None:
            self.var_session = aiohttp.ClientSession()
        return self.var_session
    
    async def get_json_rsp(self, rsp, url):
        if rsp.status == 200:
            # json_response = await response.json(content_type=None)
            data = await rsp.read()
            json_rsp = json.loads(data)
            if isinstance(json_rsp, dict) and 'code' in json_rsp:
                code = json_rsp['code']
                if code == 1024:
                    print('b站炸了，暂停所有请求1.5s后重试，请耐心等待')
                    await asyncio.sleep(1.5)
                    return None
                elif code == 3:
                    print('api错误，稍后重试，请反馈给作者')
                    await asyncio.sleep(1)
                    return None
            return json_rsp
        elif rsp.status == 403:
            print('403频繁', url)
        return None
        
    async def session_get(self, url, headers=None, data=None, params=None):
        while True:
            try:
                async with self.session.get(url, headers=headers, data=data, params=params) as response:
                    json_rsp = await self.get_json_rsp(response, url)
                    if json_rsp is not None:
                        return json_rsp
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue
    
    async def fetch_follow_num(self, uid):
        url = f'https://api.live.bilibili.com/relation/v1/Feed/GetUserFc?follow={uid}'
        json_rsp = await self.session_get(url)
        if not json_rsp['code'] and 'fc' in json_rsp['data']:
            # int
            return json_rsp['data']['fc']
        else:
            print(f'{uid}的用户获取过程中发生错误，{json_rsp}')
    
    async def fetch_room_info(self, roomid):
        url = f'https://api.live.bilibili.com/room/v1/Room/room_init?id={roomid}'
        json_rsp = await self.session_get(url)
        if not json_rsp['code']:
            # int, int
            return json_rsp['data']['room_id'], json_rsp['data']['uid']
        elif json_rsp['code'] == 60004:
            return None, None
        else:
            print(f'{roomid}的房间获取过程中发生错误，{json_rsp}')
            sys.exit(-1)


async def save_one(room_min, room_max):
    # 0 400 收录 0-399
    # 400 1200  收录 400-1199
    # room_min, room_max必须被400整除
    webhub = WebHub()
    list_rooms = []
    step = 400
    for i in range(room_min, room_max, step):
        await asyncio.sleep(0.1)
        tasklist = []
        for roomid in range(i, i + step):
            task = asyncio.ensure_future(webhub.fetch_room_info(roomid))
            tasklist.append(task)
        if tasklist:
            results = await asyncio.gather(*tasklist)
            for real_roomid, uid in results:
                if real_roomid is not None:
                    list_rooms.append((real_roomid, uid))
        print(f'当前一共{len(list_rooms)}个房间({room_min}-{i+step-1})')

    await webhub.var_session.close()

    print(f'一共{len(list_rooms)}个房间')
    list_rooms = list(set(list_rooms))
    print(f'一共{len(list_rooms)}个房间')
    
    dict_title = {'roomid': list_rooms}

    with open(f'{room_min}-{room_max-1}({len(list_rooms)}).toml', 'w', encoding="utf-8") as f:
        toml.dump(dict_title, f)
 
               
def init_min(min_room, max_room, step):
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    finished_range_mins = []
    for f in files:
        if ').toml' in f:
            print(f'找到文件{f}')
            finished_range_mins.append(int(f.split('-')[0]))
    for i in range(min_room, max_room, step):
        if i not in finished_range_mins:
            print('初始化', i)
            return i
        
async def save_all():
    min_room = 0
    max_room = 14000000
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
