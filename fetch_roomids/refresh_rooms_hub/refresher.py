from printer import info as print


class Refresher:
    NAME = 'NULL'

    # 每次获取新的房间首先要先refresh
    async def refresh(self) -> list:
        pass

    # 获取新房间从这里拿数据
    async def get_rooms(self) -> list:
        print(f'正在刷新{self.NAME}的房间')
        rooms = await self.refresh()
        print(f'{self.NAME} 获取到 {len(rooms)} 个房间')
        return rooms

    # 查看状态
    def status(self) -> dict:
        pass

    # 后台长运行
    async def run(self):
        pass
