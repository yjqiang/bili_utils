# 弹幕抽奖，后台运行
from typing import Dict
import asyncio

import attr
from aiohttp import ClientSession

import utils
from static_rooms import var_static_room_checker
from refresher import Refresher
from danmu.bili_danmu_monitor import DanmuRaffleMonitor
from tasks.utils import UtilsTask


@attr.s(slots=True)
class DanmuRoom:
    # 保持有效的时间
    GUARD_DELAY = 3600 * 24 * 15
    TV_DELAY = 3600 * 24 * 7
    STORM_DELAY = 3600 * 24 * 15

    real_roomid = attr.ib(validator=attr.validators.instance_of(int))
    latest_guard_time = attr.ib(default=0, validator=attr.validators.instance_of(int))
    latest_tv_time = attr.ib(default=0, validator=attr.validators.instance_of(int))
    latest_storm_time = attr.ib(default=0, validator=attr.validators.instance_of(int))

    @property
    def weight(self) -> int:
        curr_time = utils.curr_time()
        weight = 0
        if self.latest_guard_time + self.GUARD_DELAY > curr_time:
            weight += 6
        if self.latest_tv_time + self.TV_DELAY > curr_time:
            weight += 1
        if self.latest_storm_time + self.STORM_DELAY > curr_time:
            weight += 2
        return weight

    def update(self, raffle_type: str):
        if raffle_type == 'GUARD':
            self.latest_guard_time = utils.curr_time()
        if raffle_type == 'TV':
            self.latest_tv_time = utils.curr_time()
        if raffle_type == 'STORM':
            self.latest_storm_time = utils.curr_time()


class DanmuRoomChecker(Refresher):
    NAME = 'DANMU'

    def __init__(self):
        self.dict_danmu_rooms: Dict[int, DanmuRoom] = {}
        self.static_rooms = var_static_room_checker.rooms

    def add2rooms(self, real_roomid: int, raffle_type: str):
        if real_roomid in self.static_rooms:
            return
        # print(f'正在刷新{real_roomid}（未存在于静态房间）')
        if real_roomid in self.dict_danmu_rooms:
            danmu_room = self.dict_danmu_rooms[real_roomid]
        else:
            danmu_room = DanmuRoom(real_roomid=real_roomid)
            self.dict_danmu_rooms[real_roomid] = danmu_room

        danmu_room.update(raffle_type)
        # print(f'已经加入或更新{real_roomid}')

    async def refresh(self):
        rooms = [real_roomid for real_roomid in self.dict_danmu_rooms.keys()]
        rooms.sort(key=lambda real_roomid: self.dict_danmu_rooms[real_roomid].weight, reverse=True)
        rooms = rooms[:1500]  # 防止过多
        assert len(rooms) == len(set(rooms))

        self.dict_danmu_rooms = {real_roomid: self.dict_danmu_rooms[real_roomid] for real_roomid in rooms}
        return rooms

    def status(self) -> dict:
        return {
            'danmu_realtime': len(self.dict_danmu_rooms)
        }

    async def run(self):
        loop = asyncio.get_event_loop()
        # 弹幕运行
        session = ClientSession()
        tasks = []
        for area_id in await UtilsTask.fetch_blive_areas():
            monitor = DanmuRaffleMonitor(
                room_id=0,
                area_id=area_id,
                session=session,
                add2rooms=self.add2rooms
            )
            tasks.append(loop.create_task(monitor.run()))
        await asyncio.wait(tasks)


var_danmu_rooms_checker = DanmuRoomChecker()
