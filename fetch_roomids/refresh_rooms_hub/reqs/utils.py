from web_session import var_session

API_LIVE = 'https://api.live.bilibili.com'


class UtilsReq:
    @staticmethod
    async def fetch_blive_areas():
        url = f'{API_LIVE}/room/v1/Area/getList'
        rsp = await var_session.request_json('GET', url)
        return rsp

    @staticmethod
    async def init_room(roomid):
        url = f"{API_LIVE}/room/v1/Room/room_init?id={roomid}"
        response = await var_session.request_json('GET', url)
        return response
        
    @staticmethod
    async def get_rooms_by_area(areaid):
        url = f'{API_LIVE}/room/v1/area/getRoomList?platform=web&parent_area_id={areaid}&cate_id=0&area_id=0&sort_type=online&page=1&page_size=15'
        json_rsp = await var_session.request_json('GET', url)
        return json_rsp
        
    @staticmethod
    async def get_room_info(roomid):
        url = f"{API_LIVE}/room/v1/Room/get_info?room_id={roomid}"
        json_rsp = await var_session.request_json('GET', url)
        return json_rsp

    @staticmethod
    async def fetch_rooms_from_bili(url, page_id):
        json_rsp = await var_session.request_json('GET', f'{url}{page_id}')
        return json_rsp

    @staticmethod
    async def add_new_roomids(client, data):
        json_rsp = await var_session.request_json('POST', f'{client}/add_new_roomids', json=data)
        return json_rsp

    @staticmethod
    async def check_client(client):
        json_rsp = await var_session.request_json('GET', f'{client}/check')
        return json_rsp
