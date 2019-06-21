from typing import Dict

import attr

import utils
from printer import info as print
from static_rooms import var_static_room_checker


@attr.s
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


class DanmuRoomChecker:
    def __init__(self):
        self.dict_danmu_rooms: Dict[int, DanmuRoom] = {}
        self.rooms = []
        self.static_rooms = var_static_room_checker.get_rooms()

    def add2rooms(self, real_roomid: int, raffle_type: str):
        if real_roomid in self.static_rooms:
            print('弹幕推送命中静态房间')
            return
        if real_roomid in self.dict_danmu_rooms:
            danmu_room = self.dict_danmu_rooms[real_roomid]
        else:
            danmu_room = DanmuRoom(real_roomid=real_roomid)
            self.dict_danmu_rooms[real_roomid] = danmu_room

        danmu_room.update(raffle_type)
        print(f'已经加入或更新{real_roomid}')

    async def refresh(self):
        print('正在重新刷新DANMU房间')
        self.dict_danmu_rooms = {key: value for key, value in self.dict_danmu_rooms.items() if value.weight}

        danmu_rooms = [i for i in self.dict_danmu_rooms.values()]
        danmu_rooms.sort(key=lambda danm_room: danm_room.weight, reverse=True)

        rooms = [danmu_room.real_roomid for danmu_room in danmu_rooms][:3500]  # 防止过多
        assert len(rooms) == len(set(rooms))
        self.dict_danmu_rooms = {room: value for room, value in self.dict_danmu_rooms.items() if room in rooms}
        self.rooms = rooms

    def get_rooms(self) -> list:
        print(f'弹幕获取 {len(self.rooms)}')
        return self.rooms

    def status(self) -> dict:
        return {
            'danmu_rooms_num': len(self.rooms),
        }


var_danmu_rooms_checker = DanmuRoomChecker()
