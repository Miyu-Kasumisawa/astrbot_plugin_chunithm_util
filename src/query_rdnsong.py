import os
import json
import random

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import astrbot.api.message_components as Comp

from ..config import Config
from .utils.songutil import SongUtil

SONGS_PATH = os.path.join(Config.DATA_PATH, Config.SONG_PATH)
COVER_CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache', 'covers')

async def queryRdnSong(event: AstrMessageEvent):
    '''随机一曲
    
    Args:
        event (AstrMessageEvent): 事件上下文
    Returns:
        None: 无返回值
    '''
    
    songs = []
    with open(SONGS_PATH, "r", encoding="utf-8-sig") as file:
        songs = json.load(file)
        
    song = random.choice(songs)
    
    # songutil = SongUtil()
    # songutil.checkIsHit(os.getenv('COVER_URL'), song.get('imageName'))
    # img_conponent = await Image.from_local(os.path.join(COVER_CACHE_DIR, song.get('imageName') + ".webp"))
    # msg_chain = MessageChain([Plain(f"c{songs.index(song)} - {song.get('title')}\nby {song.get('artist')}")])
    # for sheet in song.get('sheets'):
    #     msg_chain.append(Plain(f"\n{str(sheet.get('difficulty')).capitalize()} {sheet.get('internalLevelValue')}"))
    # msg_chain.append(img_conponent)
    # await ctx.reply(msg_chain)
    
    yield event.plain_result("Not implemented yet.")