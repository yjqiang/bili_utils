import asyncio
from itertools import zip_longest
from random import shuffle
from os import path

import rsa
from aiohttp import web

import utils
from tasks.utils import UtilsTask
from static_rooms import var_static_room_checker


loop = asyncio.get_event_loop()
distributed_clients = []  # eg: ['http://127.0.0.1:8003',]


class WebServer:
    def __init__(self, admin_privkey: rsa.PrivateKey):
        self.rooms = []
        self.latest_refresh = ''
        self.latest_refresh_dyn_num = []
        self.static_rooms = var_static_room_checker.get_rooms()
        self.admin_privkey = admin_privkey
        self.remain_roomids = 0

    async def intro(self, _):
        data = {
            'code': 0,
            'version': '1.0.0b1',
            'online_rooms_latest_refresh': self.latest_refresh,
            'online_rooms_num': self.latest_refresh_dyn_num,
            'remain_roomids': self.remain_roomids
        }
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

    async def refresh(self):
        print(f'正在刷新查看ONLINE房间')
        latest_refresh_start = utils.timestamp()
        base_url = 'http://api.live.bilibili.com'
        urls = [
            f'{base_url}/room/v1/Area/getListByAreaID?areaId=0&sort=online&pageSize=170&page=',
            f'{base_url}/room/v1/room/get_user_recommend?page_size=170&page=',
        ]
        roomlists = [await UtilsTask.fetch_rooms_from_bili(urls[0])]
        for url in urls[1:]:
            await asyncio.sleep(6)
            roomlists.append(await UtilsTask.fetch_rooms_from_bili(url))

        dyn_rooms = []
        for rooms in zip_longest(*roomlists):  # 这里是为了保持优先级
            for room in rooms:
                if room and room not in dyn_rooms:
                    dyn_rooms.append(room)

        latest_refresh_dyn_num = [len(rooms) for rooms in roomlists]
        latest_refresh_dyn_num.append(len(dyn_rooms))
        self.latest_refresh_dyn_num = latest_refresh_dyn_num
        latest_refresh_end = utils.timestamp()
        self.latest_refresh = f'{latest_refresh_start} to {latest_refresh_end}'
        self.rooms = dyn_rooms
        
    async def push_roomids(self) -> float:  # 休眠时间
        print('正在推送房间')
        shuffle(distributed_clients)
        rooms = [i for i in self.rooms if i not in self.static_rooms]  # 过滤出静态房间

        roomids_monitored = []  # 所有的正在监控的房间
        remain_roomids = []  # 每个 client 的空余量
        for client in distributed_clients:
            data = await UtilsTask.check_client(client)
            remain_roomids.append(data['remain_roomids'])
            roomids_monitored += data['roomids_monitored']

        new_roomids = list(set(rooms) - set(roomids_monitored))

        if new_roomids:
            sleep_time = 0
            cursor = 0
            for i, client in enumerate(distributed_clients):
                if cursor >= len(new_roomids):
                    break
                roomid_sent = new_roomids[cursor: cursor+remain_roomids[i]]
                cursor += remain_roomids[i]
                sleep_time = max(sleep_time, await UtilsTask.add_new_roomids(client, self.admin_privkey, roomid_sent))
            self.remain_roomids = max(self.remain_roomids, len(new_roomids) - cursor)
            return sleep_time
        return 0


async def init():
    key_path = f'{path.dirname(path.realpath(__file__))}/key'
    with open(f'{key_path}/admin_privkey.pem', 'rb') as f:
        admin_privkey = rsa.PrivateKey.load_pkcs1(f.read())

    app = web.Application()
    webserver = WebServer(admin_privkey)
    app.router.add_get('/', webserver.intro)
    app.router.add_get('/is_in/{roomid}', webserver.check_index)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 9000)
    await site.start()

    wanted_time = 0
    while True:
        await webserver.refresh()
        await asyncio.sleep(wanted_time-utils.curr_time()+3)
        wanted_time = utils.curr_time() + await webserver.push_roomids()


loop.run_until_complete(init())
loop.run_forever()
