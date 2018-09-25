import asyncio
import aiohttp
import sys
import json


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
            data = json_rsp['data']
            short_id = data["short_id"]
            if short_id and short_id == roomid:
                # print(data)
                return None, None
            # int, int
            return data['room_id'], data['uid']
        elif json_rsp['code'] == 60004:
            return None, None
        else:
            print(f'{roomid}的房间获取过程中发生错误，{json_rsp}')
            sys.exit(-1)
            
    async def fetch_fan_gifts(self, roomid, uid):
        url = f'https://api.live.bilibili.com/AppRoom/getGiftTop?room_id={roomid}'
        json_rsp = await self.session_get(url)
        # print(len(json_rsp['data']['list']), roomid)
        if not json_rsp['code']:
            # int, int
            return len(json_rsp['data']['list']), roomid, uid
        else:
            print(f'{roomid}的房间获取过程中发生错误，{json_rsp}')
            sys.exit(-1)
