'''
save_all 查找readable开头的toml文件
save_one 对每个readable文件分批次运行，400一个批次，全部运行后，保存toml
输出文件为[(roomid, follower_num), (roomid, follower_num) ...], 过滤了粉丝少于1000的主播
'''
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
    
    async def fetch_follow_num(self, real_roomid, uid):
        while True:
            url = f'https://api.live.bilibili.com/relation/v1/Feed/GetUserFc?follow={uid}'
            json_rsp = await self.session_get(url)
            if not json_rsp['code'] and 'fc' in json_rsp['data']:
                # int
                return real_roomid, json_rsp['data']['fc']
            elif json_rsp['code'] == -1:
                print(f'{uid}的用户获取过程中发生错误，{json_rsp}, 稍后重试，如果一直刷请反馈')
            else:
                print(f'{uid}的用户获取过程中发生错误，{json_rsp}, 请反馈')
                sys.exit(-1)
            await asyncio.sleep(1)
    
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
            
                        
async def save_one(file_url, chuncks_roomid):
    webhub = WebHub()
    list_rooms = []
    for i, piece in enumerate(chuncks_roomid):
        await asyncio.sleep(0.1)
        tasklist = []
        for roomid, uid in piece:
            task = asyncio.ensure_future(webhub.fetch_follow_num(roomid, uid))
            tasklist.append(task)
        if tasklist:
            results = await asyncio.gather(*tasklist)
            for real_roomid, follow_num in results:
                if follow_num > 1000:
                    list_rooms.append((real_roomid, follow_num))
        print(f'当前一共{len(list_rooms)}个房间({file_url}第{i}批次)')

    await webhub.var_session.close()

    print(f'一共{len(list_rooms)}个房间')
    
    dict_title = {'roomid': list_rooms}
    
    file_url = file_url.split('.')[0]

    with open(f'follower_{file_url[9:]}_{len(list_rooms)}.toml', 'w', encoding="utf-8") as f:
        toml.dump(dict_title, f)
 
                        
async def save_all():
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    file_urls = []
    for f in files:
        if ').toml' in f and f[:9] == 'readable_':
            print(f'找到文件{f}')
            file_urls.append(f)
    for file_url in file_urls:
        with open(file_url, encoding="utf-8") as f:
            dic_roomid = toml.load(f)
        roomids = dic_roomid['roomid']
        num_roomid = len(roomids) / 2
        print('检查string去括号数据', file_url, num_roomid)
        num_roomid = int(num_roomid)
        list_tuple_roomid_uid = []
        for i in range(0, num_roomid):
            roomid = roomids[2 * i]
            uid = roomids[2 * i + 1]
            list_tuple_roomid_uid.append((roomid, uid))
        len_list_tuple_roomid_uid = len(list_tuple_roomid_uid)
        print('检查tuple数据', file_url, len_list_tuple_roomid_uid)
        chuncks = [list_tuple_roomid_uid[x: x+400] for x in range(0, len_list_tuple_roomid_uid, 400)]
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
