import asyncio
from itertools import zip_longest

from printer import info as print
from tasks.utils import UtilsTask
import utils
from static_rooms import var_static_room_checker


class OnlineRoomChecker:
    def __init__(self):
        self.page_size = 100  # 默认 100
        self.rooms = []
        self.latest_refresh = ''
        assert len(self.rooms) == len(set(self.rooms))
        self.latest_refresh_dyn_num = []
        self.static_rooms = var_static_room_checker.get_rooms()

    async def refresh(self):
        print(f'正在刷新查看ONLINE房间')
        latest_refresh_start = utils.timestamp()
        base_url = 'http://api.live.bilibili.com'
        urls = [
            f'{base_url}/room/v1/Area/getListByAreaID?areaId=0&sort=online&pageSize={self.page_size}&page=',
            f'{base_url}/room/v1/room/get_user_recommend?page_size={self.page_size}&page=',
        ]
        roomlists = [await UtilsTask.fetch_rooms_from_bili(urls[0])]
        for url in urls[1:]:
            await asyncio.sleep(6)
            roomlists.append(await UtilsTask.fetch_rooms_from_bili(url))

        '''
        max_len = max(len(rooms) for rooms in roomlists)
        if max_len >= 2000:
            dyn_rooms = []
        else:
            dyn_rooms = self.rooms[:2000-max_len]  # 延时操作，房间很多的时候，就减少比重
        '''
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

    def get_rooms(self) -> list:
        print(f'动态获取 {len(self.rooms)}')
        return self.rooms

    def status(self) -> dict:
        return {
            'online_rooms_latest_refresh': self.latest_refresh,
            'online_rooms_num': self.latest_refresh_dyn_num
        }


var_online_room_checker = OnlineRoomChecker()
