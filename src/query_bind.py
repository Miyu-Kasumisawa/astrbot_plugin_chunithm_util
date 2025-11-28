import os
import os.path as osp
import json

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import astrbot.api.message_components as Comp

from ..main import Config
from .utils.songutil import *
from .utils.apicaller import *

SONGS_PATH = os.path.join(Config.DATA_PATH, Config.SONG_PATH)
LX_JSON_PATH = osp.join(osp.dirname(__file__), '..', 'data', 'lx.json')
RIN_JSON_PATH = osp.join(osp.dirname(__file__), '..', 'data', 'rin.json')

class LXQueryBind():
    def __init__(self, event: AstrMessageEvent):
        self.event = event
        self.user_id = event.get_sender_id()
        
    async def readUsersJson(self):
        users = {}
        with open(LX_JSON_PATH, 'r') as f:
            users = json.load(f).get('users', {})
        return users
    
    def checkIsBind(self, users: dict):
        return self.user_id in users.keys()
    
    async def writeUsersJson(self, users: dict):
        try:
            with open(LX_JSON_PATH, 'w') as f:
                json.dump({'users': users}, f, indent=4)
            return 0
        except Exception as e:
            yield self.event.plain_result(f'写入失败：{e}')
            return -1
    
    async def bindAccount(self, token: str):
        users = await self.readUsersJson()
        # 检查是否已绑定
        if self.checkIsBind(users):
            users[self.user_id] = token
            await self.writeUsersJson(users)
            yield self.event.plain_result('已将原TOKEN替换为新TOKEN，请及时撤回个人TOKEN')
            return
        # 绑定账号
        users[self.user_id] = token
        await self.writeUsersJson(users)
        yield self.event.plain_result('绑定成功，请及时撤回个人TOKEN')

class RinQueryBind():
    def __init__(self, event: AstrMessageEvent):
        self.event = event
        self.user_id = event.get_sender_id()
        
    async def readUsersJson(self):
        users = {}
        with open(RIN_JSON_PATH, 'r') as f:
            users = json.load(f).get('users', {})
        return users
    
    def checkIsBind(self, users: dict):
        return self.user_id in users.keys()
    
    async def writeUsersJson(self, users: dict):
        try:
            with open(RIN_JSON_PATH, 'w') as f:
                json.dump({'users': users}, f, indent=4)
            return 0
        except Exception as e:
            yield self.event.plain_result(f'写入失败：{e}')
            return -1
    
    async def bindAccount(self, token: str):
        users = await self.readUsersJson()
        # 检查是否已绑定
        if self.checkIsBind(users):
            users[self.user_id] = token
            await self.writeUsersJson(users)
            yield self.event.plain_result('已将原卡号替换为新卡号，请及时撤回个人卡号')
            return
        # 绑定账号
        users[self.user_id] = token
        await self.writeUsersJson(users)
        yield self.event.plain_result('绑定成功，请及时撤回个人卡号')

async def queryBind(event: AstrMessageEvent, server: str, token: str):
    '''绑定'''
    match server:
        case 'lx':
            if token is None:
                await event.reply(MessageChain([Plain(f"请输入{server}服务器的token")]))
                return
            lqb = LXQueryBind(event)
            await lqb.bindAccount(token)
        case 'rin':
            if token is None:
                await event.reply(MessageChain([Plain(f"请输入{server}服务器的卡号")]))
                return
            rqb = RinQueryBind(event)
            await rqb.bindAccount(token)
        case _:
            yield event.plain_result(f"未知服务器{server}")
            return