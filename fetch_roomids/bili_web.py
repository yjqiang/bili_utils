import asyncio
import sys

import aiohttp


class WebHub:
    
    def __init__(self):
        self.var_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3))

    @staticmethod
    async def __get_json_body(rsp):
        return await rsp.json(content_type=None)

    async def __request(self, parse_rsp, method, url, **kwargs):
        i = 0
        while True:
            i += 1
            if i >= 10:
                print(url)
            try:
                async with self.var_session.request(method, url, **kwargs) as rsp:
                    if rsp.status == 200:
                        body = await parse_rsp(rsp)
                        if body:  # 有时候是None或空，直接屏蔽。下面的read/text类似，禁止返回空的东西
                            return body
                    elif rsp.status in (412, 403):
                        print(f'403频繁, {url}')
                        await asyncio.sleep(240)
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
            await asyncio.sleep(0.02)

    async def request_json(self,
                           method,
                           url,
                           **kwargs) -> dict:
        while True:
            body = await self.__request(self.__get_json_body, method, url, **kwargs)
            if not isinstance(body, dict):  # 这里是强制定制的，与b站配合的！！！！
                continue
            if body['code'] == 1024:
                print('b站炸了，暂停所有请求1.5s后重试，请耐心等待')
                await asyncio.sleep(1.0)
            else:
                return body
    
    async def fetch_follow_num(self, uid):
        while True:
            url = f'https://api.live.bilibili.com/relation/v1/Feed/GetUserFc?follow={uid}'
            json_rsp = await self.request_json('GET', url)
            if not json_rsp['code'] and 'fc' in json_rsp['data']:
                # int
                return json_rsp['data']['fc']
            elif json_rsp['code'] == -1:
                print(f'{uid}的用户获取过程中发生错误，{json_rsp}, 稍后重试，如果一直刷请反馈')
            else:
                print(f'{uid}的用户获取过程中发生错误，{json_rsp}, 请反馈')
                sys.exit(-1)
            await asyncio.sleep(1)

    async def fetch_guard_num(self, uid) -> int:
        while True:
            url = f'https://api.live.bilibili.com/guard/topList?ruid={uid}'
            json_rsp = await self.request_json('GET', url)
            if not json_rsp['code'] and 'info' in json_rsp['data']:
                info = json_rsp['data']['info']
                if 'num' in info:
                    # int
                    return int(info['num'])
            else:
                print(f'{uid}的用户获取过程中发生错误，{json_rsp}, 请反馈')
                sys.exit(-1)
            print(json_rsp)
            await asyncio.sleep(1)
    
    async def fetch_room_info(self, roomid):
        url = f'https://api.live.bilibili.com/room/v1/Room/room_init?id={roomid}'
        json_rsp = await self.request_json('GET', url)
        if not json_rsp['code']:
            data = json_rsp['data']
            short_id = data["short_id"]
            if short_id and short_id == roomid:
                # print(data)
                return None
            # int, int
            return data['uid']
        elif json_rsp['code'] == 60004:
            return None
        elif json_rsp['code'] == 60005:
            with open('bili.log', 'a', encoding='utf-8') as f:
                f.write(f'{json_rsp} {roomid}\n')
            return None
        else:
            print(f'{roomid}的房间获取过程中发生错误，{json_rsp}')
            sys.exit(-1)
            
    async def fetch_fan_gifts(self, roomid):
        url = f'https://api.live.bilibili.com/AppRoom/getGiftTop?room_id={roomid}'
        json_rsp = await self.request_json('GET', url)
        # print(len(json_rsp['data']['list']), roomid)
        if not json_rsp['code']:
            # int, int
            return len(json_rsp['data']['list'])
        else:
            print(f'{roomid}的房间获取过程中发生错误，{json_rsp}')
            sys.exit(-1)
