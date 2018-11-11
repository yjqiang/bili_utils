import aiohttp
import json
import asyncio
import sys


class BiliNet():
    def __init__(self):
        self.var_other_session = None
        
    @property
    def other_session(self):
        if self.var_other_session is None:
            self.var_other_session = aiohttp.ClientSession()
            # print(0)
        return self.var_other_session
        
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
                elif code != 0:
                    print(json_rsp)
                    return None
            return json_rsp
        elif rsp.status == 403:
            print('403频繁', url)
        return None
                
    async def other_session_get(self, url, headers=None):
        while True:
            try:
                async with self.other_session.get(url, headers=headers) as response:
                    json_rsp = await self.get_json_rsp(response, url)
                    if json_rsp is not None:
                        return json_rsp
            except:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)
                continue
        
    async def get_roomids(self, url, page_id):
        json_rsp = await self.other_session_get(f'{url}{page_id}')
        return json_rsp
        

