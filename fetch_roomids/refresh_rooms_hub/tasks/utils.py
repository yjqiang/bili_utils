import random
import asyncio

import printer
import utils
from reqs.utils import UtilsReq


class UtilsTask:
    @staticmethod
    async def is_normal_room(roomid):
        if not roomid:
            return True
        json_response = await UtilsReq.init_room(roomid)
        if not json_response['code']:
            data = json_response['data']
            param1 = data['is_hidden']
            param2 = data['is_locked']
            param3 = data['encrypted']
            if any((param1, param2, param3)):
                printer.infos([f'抽奖脚本检测到房间{roomid:^9}为异常房间'])
                return False
            else:
                printer.infos([f'抽奖脚本检测到房间{roomid:^9}为正常房间'])
                return True
    
    @staticmethod
    async def get_room_by_area(area_id, room_id=None):
        # None/0 都不行
        if room_id is not None and room_id:
            if await UtilsTask.is_ok_as_monitor(room_id, area_id):
                return room_id
        if area_id == 1:
            room_id = 23058
            if await UtilsTask.is_ok_as_monitor(room_id, area_id):
                return room_id
                
        while True:
            json_rsp = await UtilsReq.get_rooms_by_area(area_id)
            data = json_rsp['data']
            room_id = random.choice(data)['roomid']
            if await UtilsTask.is_ok_as_monitor(room_id, area_id):
                return room_id
                
    @staticmethod
    async def is_ok_as_monitor(room_id, area_id):
        json_response = await UtilsReq.init_room(room_id)
        data = json_response['data']
        is_hidden = data['is_hidden']
        is_locked = data['is_locked']
        is_encrypted = data['encrypted']
        is_normal = not any((is_hidden, is_locked, is_encrypted))
                
        json_response = await UtilsReq.get_room_info(room_id)
        data = json_response['data']
        is_open = True if data['live_status'] == 1 else False
        current_area_id = data['parent_area_id']
        # print(is_hidden, is_locked, is_encrypted, is_open, current_area_id)
        is_ok = (area_id == current_area_id) and is_normal and is_open
        return is_ok

    @staticmethod
    async def fetch_rooms_from_bili(url):
        rooms = []
        for page in range(1, 40):
            if not (page % 20):
                print(f'{url}截止第{page}页，获取{len(rooms)}个房间(可能重复)')

            json_rsp = await UtilsReq.fetch_rooms_from_bili(url, page)
            data = json_rsp['data']

            if not data:
                print(f'{url}截止结束页（第{page}页），获取{len(rooms)}个房间(可能重复)')
                break
            for room in data:
                rooms.append(int(room['roomid']))
            await asyncio.sleep(0.17)

        print('去重之前', len(rooms))
        unique_rooms = []
        for room_id in rooms:
            if room_id not in unique_rooms:
                unique_rooms.append(room_id)
        print('去重之后', len(unique_rooms))
        return unique_rooms


    @staticmethod
    async def add_new_roomids(client, privkey, room_ids):
        dict_signature = utils.make_signature(
            'SERVER',
            privkey,
            need_name=True)

        data = {
            'code': 0,
            'data': {
                'new_roomids': room_ids
            },
            'verification': dict_signature
        }
        json_rsp = await UtilsReq.add_new_roomids(client, data)
        return json_rsp['data']['sleep_time']

    @staticmethod
    async def check_client(client):
        json_rsp = await UtilsReq.check_client(client)
        return json_rsp['data']


