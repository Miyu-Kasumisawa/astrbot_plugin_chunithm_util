import os
import json

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import astrbot.api.message_components as Comp

from ..config import Config
from .utils.searcher import Searcher
from .utils.songutil import SongUtil

SONGS_PATH = os.path.join(Config.DATA_PATH, Config.SONG_PATH)

async def queryArtist(event: AstrMessageEvent, artist: str):
    '''查询曲师所有作品
    
    Args:
        event (AstrMessageEvent): 事件上下文
        artist (str): 曲师名称
    Returns:
        None: 无返回值
    '''
    
    songs = []
    matched_artists = []
    
    with open(SONGS_PATH, "r", encoding="utf-8-sig") as file:
        songs = json.load(file)
    
    searcher = Searcher()
    songutil = SongUtil()
    
    matched_artists = searcher.generalFuzzySearch(artist, songutil.getArtists(songs))
    
    if len(matched_artists) == 0:
        yield event.plain_result(f"没有找到{artist}，请尝试输入曲师全称")
        return
    
    elif len(matched_artists) == 1:
        artist_name = matched_artists[0]
        songs_by_artist = songutil.getSongsByArtist(artist_name, songs)
        msg_chain = [Comp.Plain(f"曲师 - {artist_name}作品列表：\n")]
        for song in songs_by_artist:
            msg_chain.append(Comp.Plain(f"· c{song.get('idx')} - {song.get('title')}\n"))
        yield event.chain_result(msg_chain) # type: ignore
    
    else:
        msg_chain = [Comp.Plain(f"有多个曲师符合条件\n")]
        for artist in matched_artists:
            msg_chain.append(Comp.Plain(f"· {artist}\n"))
        msg_chain.append(Comp.Plain(f"\n请使用“chu曲师 [曲师全名]”进行查询"))
        yield event.chain_result(msg_chain) # type: ignore
    return