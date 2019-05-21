import toml

from printer import info as print


class StaticRoomChecker:
    def __init__(self):
        with open('conf/roomid.toml', encoding="utf-8") as f:
            dic_roomid = toml.load(f)
        self.rooms = [int(i) for i in dic_roomid['roomid']]
        assert len(self.rooms) == len(set(self.rooms))

    @staticmethod
    async def refresh():
        print('正在重新刷新STATIC房间')
        return

    def get_rooms(self) -> list:
        return self.rooms

    def status(self) -> dict:
        return {
            'static_rooms_num': len(self.rooms),
        }


var_static_room_checker = StaticRoomChecker()
