import asyncio
import toml
from itertools import zip_longest
from datetime import datetime
from aiohttp import web
from bili_net import BiliNet


class WebServer():
    def __init__(self):
        with open('conf/roomid.toml', encoding="utf-8") as f:
            dic_roomid = toml.load(f)
        self.static_rooms = dic_roomid['roomid']
        self.dyn_rooms = self.static_rooms
        self.net = BiliNet()
        self.latest_refresh = '0 to 0'
        self.latest_refresh_dyn_num = []
        print('static rooms', len(self.static_rooms))
        
    async def intro(self, request):
        data = {
            'code': 0,
            'version': '1.1.2',
            'latest_refresh': self.latest_refresh,
            'latest_refresh_dyn_num': self.latest_refresh_dyn_num
            }
        return web.json_response(data)
    
    async def hello(self, request):
        name = request.match_info.get('name', 'World')
        data = {'code': 0, 'msg': f'Hello {name}!'}
        return web.json_response(data)
        
    async def check_room(self, request):
        roomid = request.match_info['roomid']
        try:
            roomid = int(roomid)
            code = 0
            if roomid in self.dyn_rooms:
                is_in = True
                index = self.dyn_rooms.index(roomid)
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
        end = request.match_info.get('end', 6000)
        try:
            start = int(start)
            end = int(end)
            data = {'code': 0, 'roomid': self.dyn_rooms[start:end]}
        except ValueError:
            data = {'code': -1, 'roomid': []}
        
        return web.json_response(data)
        
    async def refresh(self):
        latest_refresh_start = timestamp()
        async def fetch_room(url):
            rooms = []
            for page in range(1, 250):
                if not (page % 30):
                    print(f'截止第{page}页，获取了{len(rooms)}个房间(可能重复)')
                
                json_rsp = await self.net.get_roomids(url, page)
                data = json_rsp['data']
                online_num = [room['online'] for room in data]
                if not data or max(online_num) <= 100:
                    print(f'截止第{page}页，获取了{len(rooms)}个房间(可能重复)')
                    # if page <= 25:
                    #     print(json_rsp)
                    break
                for room in data:
                    # room['online']
                    rooms.append(room['roomid'])
                await asyncio.sleep(0.15)
                                    
            print('去重之前', len(rooms))
            unique_rooms = []
            for id in rooms:
                if id not in unique_rooms:
                    unique_rooms.append(id)
            print('去重之后', len(unique_rooms))
            return unique_rooms
            
        base_url = 'http://api.live.bilibili.com'
        urls = [
            f'{base_url}/area/liveList?area=all&order=online&page=',
            f'{base_url}/room/v1/room/get_user_recommend?page=',
            f'{base_url}/area/liveList?area=all&order=online&page=',
            f'{base_url}/room/v1/room/get_user_recommend?page='
        ]
        roomlists = [await fetch_room(urls[0])]
        for url in urls[1:]:
            await asyncio.sleep(6)
            roomlists.append(await fetch_room(url))

        unique_rooms = []
        for rooms in zip_longest(*roomlists):
            for room in rooms:
                if room is not None and room not in unique_rooms:
                    unique_rooms.append(room)
        print(f'动态方法总获取房间{len(unique_rooms)}')
        self.latest_refresh_dyn_num = [len(rooms) for rooms in roomlists]
        self.latest_refresh_dyn_num.append(len(unique_rooms))
        roomid_conf = self.static_rooms
        for i in roomid_conf:
            if len(unique_rooms) >= 6000:
                break
            if i not in unique_rooms:
                unique_rooms.append(i)
        print(f'合计总获取房间{len(unique_rooms)}')
        self.dyn_rooms = unique_rooms
        print(self.dyn_rooms[:10])
        self.latest_refresh = f'{latest_refresh_start} to {timestamp()}'
    

def timestamp():
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return time_now
            
async def init(loop):
    app = web.Application(loop=loop)
    webserver = WebServer()
    app.router.add_get('/', webserver.intro)
    app.router.add_get('/hello', webserver.hello)
    app.router.add_get('/hello/{name}', webserver.hello)
    
    app.router.add_get('/is_in/{roomid}', webserver.check_room)
    
    app.router.add_get('/dyn_rooms', webserver.fetch_rooms)
    app.router.add_get('/dyn_rooms/{start}-{end}', webserver.fetch_rooms)
    await loop.create_server(app.make_handler(), '0.0.0.0', 8000)
    print('Server started at port 8000...')
    await webserver.refresh()
    while True:
        now = datetime.now()
        print(f'{timestamp()}')
        if (now.minute == 0 or now.minute == 20 or now.minute == 40) and now.second <= 40:
            print('到达设定时间，正在重新查看房间')
            print(f'{timestamp()}')
            await webserver.refresh()
            print(f'{timestamp()}')
            await asyncio.sleep(60)
        await asyncio.sleep(30)
        '''
        print(f'{timestamp()}')
        await webserver.refresh()
        print(f'{timestamp()}')
        await asyncio.sleep(60)
        '''
    

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()

