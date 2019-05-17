import asyncio
import toml
from itertools import zip_longest
from datetime import datetime
from aiohttp import web
from bili_net import BiliNet


class WebServer:
    def __init__(self):
        with open('conf/roomid.toml', encoding="utf-8") as f:
            dic_roomid = toml.load(f)
        self.static_rooms = dic_roomid['roomid']
        assert len(self.static_rooms) == len(set(self.static_rooms))
        self.rooms = self.static_rooms
        self.net = BiliNet()
        self.latest_refresh = '0 to 0'
        self.latest_refresh_dyn_num = []
        print('static rooms', len(self.static_rooms))
        
    async def intro(self, _):
        data = {
            'code': 0,
            'version': '1.2.0b1',
            'latest_refresh': self.latest_refresh,
            'latest_refresh_dyn_num': self.latest_refresh_dyn_num
            }
        return web.json_response(data)
    
    @staticmethod
    async def hello(request):
        name = request.match_info.get('name', 'World')
        data = {'code': 0, 'msg': f'Hello {name}!'}
        return web.json_response(data)
        
    async def check_room(self, request):
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

    async def _fetch_rooms_from_bili(self, url):
        rooms = []
        for page in range(1, 250):
            if not (page % 20):
                print(f'{url}截止第{page}页，获取{len(rooms)}个房间(可能重复)')

            json_rsp = await self.net.get_roomids(url, page)
            data = json_rsp['data']

            if not data or max(room['online'] for room in data) <= 100:
                print(f'{url}截止结束页（第{page}页），获取{len(rooms)}个房间(可能重复)')
                break
            for room in data:
                rooms.append(room['roomid'])
            await asyncio.sleep(0.15)

        print('去重之前', len(rooms))
        unique_rooms = []
        for room_id in rooms:
            if room_id not in unique_rooms:
                unique_rooms.append(room_id)
        print('去重之后', len(unique_rooms))
        return unique_rooms
        
    async def refresh(self):
        latest_refresh_start = timestamp()
        print(f'{latest_refresh_start} 正在重新查看房间')
        base_url = 'http://api.live.bilibili.com'
        urls = [
            f'{base_url}/room/v1/Area/getListByAreaID?areaId=0&sort=online&pageSize=40&page=',
            f'{base_url}/room/v1/room/get_user_recommend?page=',
            f'{base_url}/room/v1/Area/getListByAreaID?areaId=0&sort=online&pageSize=40&page=',
            f'{base_url}/room/v1/room/get_user_recommend?page=',
        ]
        roomlists = [await self._fetch_rooms_from_bili(urls[0])]
        for url in urls[1:]:
            await asyncio.sleep(6)
            roomlists.append(await self._fetch_rooms_from_bili(url))

        dyn_rooms = []
        for rooms in zip_longest(*roomlists):
            for room in rooms:
                if room is not None and room not in dyn_rooms:
                    dyn_rooms.append(room)

        latest_refresh_dyn_num = [len(rooms) for rooms in roomlists]
        latest_refresh_dyn_num.append(len(dyn_rooms))
        self.latest_refresh_dyn_num = latest_refresh_dyn_num

        new_rooms = self.static_rooms  # 新房间先填固定房间
        for room_id in dyn_rooms:  # 填动态房间
            if room_id not in new_rooms:
                new_rooms.append(room_id)
        print(f'动态总获取房间{len(dyn_rooms)}')
        print(f'合计总获取房间{len(new_rooms)}')
        self.rooms = new_rooms
        print(f'新房间：{", ".join(map(str, self.rooms[:6]))} ... {", ".join(map(str, self.rooms[-6:]))}')
        latest_refresh_end = timestamp()
        self.latest_refresh = f'{latest_refresh_start} to {latest_refresh_end}'
        print(f'{latest_refresh_end} 结束查看房间动作')
    

def timestamp():
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return time_now


async def init():
    app = web.Application()
    webserver = WebServer()
    app.router.add_get('/', webserver.intro)
    app.router.add_get('/hello', webserver.hello)
    app.router.add_get('/hello/{name}', webserver.hello)

    app.router.add_get('/is_in/{roomid}', webserver.check_room)

    app.router.add_get('/dyn_rooms', webserver.fetch_rooms)
    app.router.add_get('/dyn_rooms/{start}-{end}', webserver.fetch_rooms)

    app.router.add_get('/rooms', webserver.fetch_rooms)
    app.router.add_get('/rooms/{start}-{end}', webserver.fetch_rooms)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await webserver.refresh()
    await site.start()
    print('Server started at port 8000...')
    while True:
        now = datetime.now()
        print(f'现在时间是 {timestamp()}')
        if now.minute in (0, 20, 40) and now.second <= 40:
            await webserver.refresh()
            await asyncio.sleep(60)
        await asyncio.sleep(30)
    

loop = asyncio.get_event_loop()
loop.run_until_complete(init())
loop.run_forever()
