import os
import os.path as osp
import json
import sqlite3

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import astrbot.api.message_components as Comp

from ..main import Config
from .query_song import searchSong
from .utils.songutil import *

SONGS_PATH = os.path.join(Config.DATA_PATH, Config.SONG_PATH)
DB_PATH = os.path.join(os.path.dirname(__file__), "..", 'data', 'data.db')
LX_JSON_PATH = osp.join(osp.dirname(__file__), '..', 'data', 'lx.json')
HELP_API_IMG_PATH = osp.join(osp.dirname(__file__), '..', 'images', 'api.png')

# ========= 落雪查分器 =========
class LXHandler:
    def __init__(self, event: AstrMessageEvent):
        self.event = event
        self.user_id = event.get_sender_id()
        self.song_url = "https://maimai.lxns.net/api/v0/chunithm/song/list"
        self.record_url = "https://maimai.lxns.net/api/v0/user/chunithm/player/scores"
    
    async def readUsersJson(self):
        users = {}
        with open(LX_JSON_PATH, 'r') as f:
            users = json.load(f).get('users', {})
        return users
    
    async def writeUsersJson(self, users: dict):
        try:
            with open(LX_JSON_PATH, 'w') as f:
                json.dump({'users': users}, f, indent=4)
            return
        except Exception as e:
            yield self.event.plain_result(f'写入用户信息失败：{e}')
            return
    
    def checkIsBind(self, users: dict):
        return self.user_id in users.keys()

    def getSongs(self) -> list:
        response = requests.get(self.song_url)
        data = response.json()
        songs = data.get('songs', [])
        return songs
    
    def updateRecord(self, user_id: str, cid: str, score: int, difficulty: int):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # 高于现有分数才更新
        c.execute(f"SELECT * FROM record WHERE user_id = ? AND cid = ? AND score > ?", (user_id, cid, score))
        if c.fetchone():
            return
        c.execute(f"INSERT OR REPLACE INTO record (user_id, cid, score, difficulty) VALUES (?, ?, ?, ?)", (user_id, cid, score, difficulty))
        conn.commit()
        conn.close()
    
    async def copyLXRecord(self):
        users = await self.readUsersJson()
        if not self.checkIsBind(users):
            img = Comp.Image(HELP_API_IMG_PATH)
            yield self.event.chain_result([
                Comp.Plain('你还没有绑定账号，请先使用“chubind [服务器] [TOKEN]”绑定账号\n（服务器暂时仅支持lx）\n\nTOKEN获取地址：https://maimai.lxns.net/user/profile'),
                img  
            ])
            return
        # 请求记录
        headers = {
            "X-User-Token": users[self.user_id],
        }
        
        response = requests.get(self.record_url, headers=headers)
        data = response.json()
        match data.get('code'):
            case 200:
                try:
                    records = data.get('data', [])
                    for record in records:
                        self.updateRecord(self.user_id, str(record.get('id')), record.get('score'), record.get('level_index'))
                    yield self.event.plain_result('迁移LX查分器数据成功')
                    return
                except Exception as e:
                    yield self.event.plain_result(f'迁移LX查分器数据失败，{e}')
                    return
            case _:
                yield self.event.plain_result(f'获取失败，请检查TOKEN是否正确')
                return
        
# ========= Rin服 =========
class RinHandler:
    def __init__(self, event: AstrMessageEvent, user_id: str):
        self.ctx = event
        self.user_id = user_id
        
    async def copyRinRecord(self, user_id: str):
        raise NotImplementedError

async def queryCopy(event: AstrMessageEvent, server: str):
    '''查询最佳
    
    Args:
        ctx (EventContext): 事件上下文
        args (list): 参数列表
    Returns:
        None: 无返回值
    '''
    match server:
        case 'lx':
            lx = LXHandler(event)
            async for _ in lx.copyLXRecord():
                pass
        case 'rin':
            yield event.plain_result(f"暂不支持{server}服务器")
            return
        case _:
            yield event.plain_result(f"未知服务器{server}")
            return