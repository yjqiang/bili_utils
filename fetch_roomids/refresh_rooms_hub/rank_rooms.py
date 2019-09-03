# rank api搜索，无限后台循环
from typing import Dict
import asyncio
from itertools import zip_longest

import attr

from tasks.utils import UtilsTask
import utils
from static_rooms import var_static_room_checker
from refresher import Refresher


@attr.s(slots=True)
class RankRoom:
    # 保持有效的时间
    DELAY = 3600 * 24 * 7

    real_roomid = attr.ib(validator=attr.validators.instance_of(int))
    latest_time = attr.ib(default=0, validator=attr.validators.instance_of(int))

    @property
    def weight(self) -> int:
        curr_time = utils.curr_time()
        weight = 0
        if self.latest_time + self.DELAY > curr_time:
            weight += self.latest_time
        return weight

    def update(self):
        self.latest_time = utils.curr_time()


class RankRoomChecker(Refresher):
    NAME = 'RANK'

    def __init__(self):
        self.urls = []
        self.reset_max_rooms_num()
        self.latest_refresh = ''
        self.latest_refresh_rank_num = []
        self.dict_rank_rooms: Dict[int, RankRoom] = {}
        self.static_rooms = var_static_room_checker.rooms

    def add2rooms(self, real_roomid: int):
        if real_roomid in self.static_rooms:
            return
        # print(f'正在刷新{real_roomid}（未存在于静态房间）')
        if real_roomid in self.dict_rank_rooms:
            danmu_room = self.dict_rank_rooms[real_roomid]
        else:
            danmu_room = RankRoom(real_roomid=real_roomid)
            self.dict_rank_rooms[real_roomid] = danmu_room

        danmu_room.update()
        # print(f'已经加入或更新{real_roomid}')

    def reset_max_rooms_num(self):  # 大约的数据
        base_url = 'http://api.live.bilibili.com'
        urls = [
            (
                f'{base_url}/rankdb/v1/Rank2018/getTop?type=master_realtime_hour&type_id=areaid_realtime_hour&page_size=12&area_id=',
                8
            ),
            (
                f'{base_url}/rankdb/v1/Rank2018/getTop?&type=master_last_hour&type_id=areaid_hour&page_size=20&area_id=0&page=',
                5
            ),
            (
                f'{base_url}/rankdb/v1/Rank2018/getTop?&type=master_last_hour&type_id=areaid_hour&page_size=20&area_id=1&page=',
                5
            ),
            (
                f'{base_url}/rankdb/v1/Rank2018/getTop?&type=master_last_hour&type_id=areaid_hour&page_size=20&area_id=2&page=',
                5
            ),
            (
                f'{base_url}/rankdb/v1/Rank2018/getTop?&type=master_last_hour&type_id=areaid_hour&page_size=20&area_id=3&page=',
                5
            ),
            (
                f'{base_url}/rankdb/v1/Rank2018/getTop?&type=master_last_hour&type_id=areaid_hour&page_size=20&area_id=4&page=',
                5
            ),
            (
                f'{base_url}/rankdb/v1/Rank2018/getTop?&type=master_last_hour&type_id=areaid_hour&page_size=20&area_id=5&page=',
                5
            ),
            (
                f'{base_url}/rankdb/v1/Rank2018/getTop?&type=master_last_hour&type_id=areaid_hour&page_size=20&area_id=6&page=',
                5
            ),
            (
                f'{base_url}/rankdb/v1/Rank2018/getTop?&type=master_last_hour&type_id=areaid_hour&page_size=20&area_id=7&page=',
                5
            )

        ]
        self.urls = urls

    def status(self) -> dict:
        return {
            'rank_rooms_latest_refresh': self.latest_refresh,
            'rank_rooms_num': self.latest_refresh_rank_num,
            'rank_realtime': len(self.dict_rank_rooms)
        }
    
    async def refresh(self):
        latest_refresh_start = utils.timestamp()
        roomlists = [await UtilsTask.fetch_rooms_from_rank(*self.urls[0])]
        for url, pages_num in self.urls[1:]:
            await asyncio.sleep(1.5)
            roomlists.append(await UtilsTask.fetch_rooms_from_rank(url, pages_num))

        rank_rooms = []
        for rooms in zip_longest(*roomlists):  # 这里是为了保持优先级
            for room in rooms:
                if room and room not in rank_rooms:
                    rank_rooms.append(room)
        for real_roomid in rank_rooms:
            self.add2rooms(real_roomid)

        latest_refresh_rank_num = [len(rooms) for rooms in roomlists]
        latest_refresh_rank_num.append(len(rank_rooms))
        self.latest_refresh_rank_num = latest_refresh_rank_num
        latest_refresh_end = utils.timestamp()
        self.latest_refresh = f'{latest_refresh_start} to {latest_refresh_end}'

        rooms = [real_roomid for real_roomid in self.dict_rank_rooms.keys()]
        rooms.sort(key=lambda real_roomid: self.dict_rank_rooms[real_roomid].weight, reverse=True)
        rooms = rooms[:2000]  # 防止过多
        assert len(rooms) == len(set(rooms))

        self.dict_rank_rooms = {real_roomid: self.dict_rank_rooms[real_roomid] for real_roomid in rooms}
        return rooms


var_rank_room_checker = RankRoomChecker()
