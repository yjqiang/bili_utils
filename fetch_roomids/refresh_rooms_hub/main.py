import asyncio
from datetime import datetime

from aiohttp import web

from danmu_rooms import var_danmu_rooms_checker
from static_rooms import var_static_room_checker
from rank_rooms import var_rank_room_checker
from printer import info as print


loop = asyncio.get_event_loop()


class RoomCheckers:
    def __init__(self):
        self.checkers = [var_static_room_checker, var_danmu_rooms_checker, var_rank_room_checker]

    async def refresh_and_get_rooms(self):
        rooms = []
        for checker in self.checkers:
            for room in await checker.get_rooms():  # 填动态房间
                if room not in rooms:
                    rooms.append(room)
        print(f'合计总获取房间{len(rooms)}')
        return rooms

    def status(self) -> dict:
        result = {}
        for check in self.checkers:
            result[check.NAME] = check.status()
        return result

    async def run(self):
        tasks = []
        for check in self.checkers:
            task = loop.create_task(check.run())
            tasks.append(task)
        await asyncio.wait(tasks)


class WebServer:
    def __init__(self):
        self.checker = RoomCheckers()
        self.rooms = []

    async def intro(self, _):
        data = {
            'code': 0,
            'version': '2.0.0b0',
            **self.checker.status()
            }
        return web.json_response(data)
    
    @staticmethod
    async def hello(request):
        name = request.match_info.get('name', 'World')
        data = {'code': 0, 'msg': f'Hello {name}!'}
        return web.json_response(data)
        
    async def check_index(self, request):
        roomid = request.match_info['roomid']
        try:
            roomid = int(roomid)
            code = 0
            if roomid in self.rooms:
                is_in = True
                index = self.rooms.index(roomid)
            else:
                is_in = False
                index = -1
        except ValueError:
            code = -1
            is_in = False
            index = -1
            
        data = {'code': code, 'is_in': is_in, 'index': index}
               
        return web.json_response(data)
                           
    async def fetch_rooms(self, request):
        start = request.match_info.get('start', 0)
        end = request.match_info.get('end', 7200)
        try:
            start = int(start)
            end = int(end)
            data = {'code': 0, 'roomid': self.rooms[start:end]}
        except ValueError:
            data = {'code': -1, 'roomid': []}
        
        return web.json_response(data)
        
    async def refresh(self):
        self.rooms = await self.checker.refresh_and_get_rooms()

    async def run(self):
        await self.checker.run()


async def init():
    app = web.Application()
    webserver = WebServer()
    app.router.add_get('/', webserver.intro)
    app.router.add_get('/hello', webserver.hello)

    app.router.add_get('/is_in/{roomid}', webserver.check_index)

    app.router.add_get('/dyn_rooms', webserver.fetch_rooms)
    app.router.add_get('/dyn_rooms/{start}-{end}', webserver.fetch_rooms)

    app.router.add_get('/rooms', webserver.fetch_rooms)
    app.router.add_get('/rooms/{start}-{end}', webserver.fetch_rooms)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)

    loop.create_task(webserver.run())

    await webserver.refresh()

    await site.start()
    print('Server started at port 8000...')

    while True:
        now = datetime.now()
        print(f'检查REFRESH是否应该开始')
        if now.minute in (0, 20, 40) and now.second <= 40:
            await webserver.refresh()
            await asyncio.sleep(60)
        await asyncio.sleep(30)
    

loop.run_until_complete(init())
loop.run_forever()
