import os
import json
import re

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import astrbot.api.message_components as Comp

from ..main import Config
from .utils.songutil import SongUtil
from .utils.aliaslogger import AliasLogger
from .query_song import searchSong

SONGS_PATH = os.path.join(Config.DATA_PATH, Config.SONG_PATH)
ALIAS_PATH = os.path.join(Config.DATA_PATH, Config.ALIAS_PATH)

async def queryAddAlias(event: AstrMessageEvent, cid: str, alias: str):
    '''添加别名
    
    Args:
        event (AstrMessageEvent): 事件上下文
        cid (str): 歌曲cid
        alias (str): 新增别名列表
    Returns:
        None: 无返回值
    '''
    
    aliases_to_add = re.split(r"[，,]", alias)
    if not re.match(r"^c\d+$", cid):
        yield event.plain_result("请使用cid进行别名添加")
        return
    matched_songs = searchSong(cid)
    if len(matched_songs) == 0:
        yield event.plain_result("未找到cid对应的歌曲，请检查cid是否正确")
        return
    elif len(matched_songs) > 1:
        songs = []
        with open(SONGS_PATH, 'r', encoding='utf-8-sig') as f:
            songs = json.load(f)
        msg_chain = [Comp.Plain(f"有多个曲目符合条件\n")]
        for cid in matched_songs:
            name = None
            for song in songs:
                if song.get('idx') == cid:
                    name = song.get('title')
                    break
            msg_chain.append(Comp.Plain(f"c{cid} - {name}\n"))
        msg_chain.append(Comp.Plain(f"\n请使用cid进行精准查询"))
        yield event.chain_result(msg_chain) # type: ignore
        return
    
    cid = matched_songs[0]
    songs = []
    with open(SONGS_PATH, 'r', encoding='utf-8-sig') as f:
        songs = json.load(f)
    
    alias_for_songs = []
    with open(ALIAS_PATH, 'r', encoding='utf-8') as f:
        alias_for_songs = json.load(f).get('songs')
    
    name = None
    for song in songs:
        if song.get('idx') == cid:
            name = song.get('title')
            break
    songutil = SongUtil()
    valid_aliases, invalid_aliases = songutil.addAlias(cid, alias_for_songs, aliases_to_add)
    
    '''记录别名添加日志'''
    aliaslogger = AliasLogger()
    aliaslogger.log({
        "user_id": event.unified_msg_origin,
        "user_name": event.get_sender_name,
        "group_id": event.get_group_id,
        "cid": f"c{cid}",
        "songId": name,
        "valid_aliases": valid_aliases,
        "invalid_aliases": invalid_aliases
    })
    
    yield event.chain_result([
        Comp.Plain(f"c{cid} - {name}的别名：{', '.join(valid_aliases)}添加成功\n")
        if len(valid_aliases) > 0 else Comp.Plain(""),
        Comp.Plain(f"c{cid} - {name}的别名：{', '.join(invalid_aliases)}已存在")
        if len(invalid_aliases) > 0 else Comp.Plain(""),
        Comp.Plain("\n添加歌曲别名将记录在日志中")
    ])

async def queryGetAlias(event: AstrMessageEvent, condition: str):
    '''获取曲目别名
    
    Args:
        event (AstrMessageEvent): 事件上下文
        condition (str): 查询条件(cid/别名)
    Returns:
        None: 无返回值
    '''
    
    matched_songs = searchSong(condition)
    songs = []
    with open(SONGS_PATH, 'r', encoding='utf-8-sig') as f:
        songs = json.load(f)
    if len(matched_songs) == 0:
        yield event.plain_result("未找到该歌曲，试着输入歌曲全称或其他别名")
        return
    elif len(matched_songs) > 1:
        msg_chain = [Comp.Plain(f"有多个曲目符合条件\n")]
        for cid in matched_songs:
            name = None
            for song in songs:
                if song.get('idx') == cid:
                    name = song.get('title')
                    break
            msg_chain.append(Comp.Plain(f"c{cid} - {name}\n"))
        msg_chain.append(Comp.Plain(f"\n请使用cid进行精准查询"))
        yield event.chain_result(msg_chain) # type: ignore
        return
    
    cid = matched_songs[0]
    name = None
    for song in songs:
        if song.get('idx') == cid:
            name = song.get('title')
            break
    
    alias_json_songs = []
    with open(ALIAS_PATH, 'r', encoding='utf-8') as f:
        alias_json_songs = json.load(f).get('songs')
    
    songutil = SongUtil()
    aliases = songutil.getAlias(cid, alias_json_songs)
    if len(aliases) == 0:
        yield event.plain_result(f"c{cid} - {name}暂无别名")
        return
    
    msg_chain = [Comp.Plain(f"c{cid} - {name}的别名：")]
    for alias in aliases:
        msg_chain.append(Comp.Plain(f"\n· {alias}"))
    msg_chain.append(Comp.Plain(f"\n别名均为用户添加，与BOT无关"))
    yield event.chain_result(msg_chain) # type: ignore

async def queryDelAlias(event: AstrMessageEvent, args: list) -> None:
    pass
