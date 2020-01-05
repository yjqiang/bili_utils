import asyncio
from typing import Optional, Callable

from aiohttp import ClientSession

from printer import info as print
from .bili_danmu import WsDanmuClient
from tasks.utils import UtilsTask


class DanmuRaffleMonitor(WsDanmuClient):
    def __init__(
            self, room_id: int, area_id: int, add2rooms: Callable,
            session: Optional[ClientSession] = None, loop=None):
        self.add2rooms = add2rooms
        super().__init__(
            room_id=room_id,
            area_id=area_id,
            session=session,
            loop=loop
        )
        self._funcs_task.append(self._check_area)  # 比正常的监控多了一个分区定时查看

    async def _check_area(self):
        try:
            while True:
                await asyncio.sleep(300)
                is_ok = await asyncio.shield(
                    UtilsTask.is_ok_as_monitor(self._room_id, self._area_id))
                if not is_ok:
                    print(f'{self._room_id}不再适合作为监控房间，即将切换')
                    return
        except asyncio.CancelledError:
            pass

    async def _prepare_client(self):
        self._room_id = await UtilsTask.get_room_by_area(
            self._area_id, self._room_id)
        print(f'{self._area_id}号数据连接选择房间（{self._room_id}）')

    def handle_danmu(self, data: dict):
        if 'cmd' in data:
            cmd = data['cmd']
        elif 'msg' in data:
            data = data['msg']
            cmd = data['cmd']
        else:
            return True  # 预防未来sbb站

        if cmd == 'PREPARING':
            print(f'{self._area_id}号数据连接房间下播({self._room_id})')
            return False

        elif cmd == 'NOTICE_MSG':
            # 1 《第五人格》哔哩哔哩直播预选赛六强诞生！
            # 2 全区广播：<%user_name%>送给<%user_name%>1个嗨翻全城，快来抽奖吧
            # 3 <%user_name%> 在 <%user_name%> 的房间开通了总督并触发了抽奖，点击前往TA的房间去抽奖吧
            # 4 欢迎 <%总督 user_name%> 登船
            # 5 恭喜 <%user_name%> 获得大奖 <%23333x银瓜子%>, 感谢 <%user_name%> 的赠送
            # 6 <%user_name%> 在直播间 <%529%> 使用了 <%20%> 倍节奏风暴，大家快去跟风领取奖励吧！(只报20的)
            msg_type = data['msg_type']
            real_roomid = int(data['real_roomid'])
            if msg_type == 2 or msg_type == 8:
                raffle_name = '小电视'
                print(f'{self._area_id}号数据连接检测到{real_roomid:^9}的{raffle_name}')
                self.add2rooms(real_roomid, 'TV')
            elif msg_type == 3:
                raffle_name = '舰队'
                print(f'{self._area_id}号数据连接检测到{real_roomid:^9}的{raffle_name}')
                self.add2rooms(real_roomid, 'GUARD')
            elif msg_type == 6:
                raffle_name = '二十倍节奏风暴'
                print(f'{self._area_id}号数据连接检测到{real_roomid:^9}的{raffle_name}')
                self.add2rooms(real_roomid, 'STORM')
        return True
