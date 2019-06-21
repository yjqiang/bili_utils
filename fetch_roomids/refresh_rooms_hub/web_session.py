import sys
import asyncio
import aiohttp
import printer
from json_rsp_ctrl import Ctrl, JsonRspType, ZERO_ONLY_CTRL

sem = asyncio.Semaphore(2)


class WebSession:
    def __init__(self):
        self.var_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=4))

    @staticmethod
    async def __get_json_body(rsp):
        json_body = await rsp.json(content_type=None)
        return json_body

    # method 类似于aiohttp里面的对应method，目前只支持GET、POST
    # is_login后期移除，json这里应该与expected_code协同
    async def request_json(self,
                           method,
                           url,
                           ctrl: Ctrl = ZERO_ONLY_CTRL,
                           **kwargs) -> dict:
        async with sem:
            i = 0
            while True:
                i += 1
                if i >= 10:
                    printer.warn(url)
                try:
                    async with self.var_session.request(method, url, **kwargs) as rsp:
                        if rsp.status == 200:
                            json_body = await self.__get_json_body(rsp)
                            if json_body:  # 有时候是None或空，直接屏蔽。下面的read/text类似，禁止返回空的东西
                                json_rsp_type = ctrl.verify(json_body)
                                if json_rsp_type == JsonRspType.OK:
                                    return json_body
                                elif json_rsp_type == JsonRspType.IGNORE:
                                    await asyncio.sleep(1.0)
                        elif rsp.status in (412, 403):
                            printer.warn(f'403频繁, {url}')
                            await asyncio.sleep(240)
                except asyncio.CancelledError:
                    raise
                except:
                    # print('当前网络不好，正在重试，请反馈开发者!!!!')
                    print(sys.exc_info()[0], sys.exc_info()[1], url)
                await asyncio.sleep(0.02)


async def exec_as_coroutine(func, *args):
    if asyncio.iscoroutinefunction(func):
        return await func(*args)
    return func(*args)


var_session = asyncio.get_event_loop().run_until_complete(exec_as_coroutine(WebSession))
