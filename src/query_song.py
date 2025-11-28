import os
import json
import re

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import astrbot.api.message_components as Comp

from ..config import Config
from .utils.songutil import SongUtil
from .utils.searcher import Searcher

SONGS_PATH = os.path.join(Config.DATA_PATH, Config.SONG_PATH)
ALIAS_PATH = os.path.join(Config.DATA_PATH, Config.ALIAS_PATH)
SEGA_SONG_PATH = os.path.join(Config.DATA_PATH, Config.SEGA_SONG_PATH)
COVER_CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache', 'covers')

def calcDate(timeStamp: int):
    '''时间戳转YEAR-MONTH-DAY'''
    import time
    timeArray = time.localtime(timeStamp*100)
    return time.strftime("%Y-%m-%d", timeArray)


def searchSong(name: str) -> list[str]:
    '''查询歌曲
    
    Args:
        name: 歌曲名
    Returns:
        cids: 匹配歌曲cid列表
    '''
    songs = []
    cids = []
    
    with open(SONGS_PATH, "r", encoding="utf-8-sig") as f:
        songs = json.load(f)
    with open(ALIAS_PATH, "r", encoding="utf-8") as f:
        alias_for_songs = json.load(f).get("songs")

    # 1. cid搜索
    if re.match(r"^c\d+$", name):
        cid = name[1:]
        if cid.isdigit():
            for song in songs:
                if song.get('idx') == cid and cid not in cids:
                    cids.append(cid)
                    break
        return cids
    
    # 2. 别名搜索 
    for song in alias_for_songs:
        for alias in song.get('aliases'):
            if alias == name:  # 别名采用精准匹配
                cids.append(song.get('cid'))
    if len(cids) > 0:  # 别名存在，直接返回
        return cids
    
    # 3. 模糊搜索
    searcher = Searcher()
    names = list(set([song.get('title') for song in songs]))
    fuzzy_matched_songs = searcher.generalFuzzySearch(name, names)
    fuzzy_matched_cids = []
    for fuzzy_matched_song in fuzzy_matched_songs:
        for song in songs:
            if song.get('title') == fuzzy_matched_song:
                fuzzy_matched_cids.append(song.get('idx'))
    cids.extend(fuzzy_matched_cids)
    
    cids = list(set(cids))
    return cids
    
def querySong(event: AstrMessageEvent, arg: str):
    '''回复歌曲查询结果
    
    Args:
        event (AstrMessageEvent): 事件上下文
        args (str): 参数
    Returns:
        None: 无返回值
    '''
    name = arg
    songs = []
    
    with open(SONGS_PATH, "r", encoding="utf-8-sig") as f:
        songs = json.load(f)
    
    matched_songs = searchSong(name)
    
    if len(matched_songs) == 1:
        target_songs = [song for song in songs if song.get('idx') == matched_songs[0]]
        song = target_songs[0]
        cid = song.get('idx')
        constants = [str(song.get('const')) for song in target_songs]
        
        songutil = SongUtil()
        songutil.checkIsHit(Config.COVER_URL, song.get('img'))
        
        img_conponent = Comp.Image(os.path.join(COVER_CACHE_DIR, song.get('img') + ".webp"))
        msg_chain = [
            Comp.Plain(f"c{cid} - {song.get('title')}\n"),
            Comp.Plain(f"曲师: {song.get('artist')}\n"),
            Comp.Plain(f"分类：{song.get('genre')}\n"),
            Comp.Plain(f"BPM: {song.get('bpm')}\n"),
            Comp.Plain(f"追加版本: {song.get('version')}\n"),
            Comp.Plain(f"发行日期: {calcDate(song.get('release'))}\n"),
            Comp.Plain(f"定数: "),
            Comp.Plain(f"{' / '.join(constants)}\n"),
            img_conponent
            ] 
        msg_chain.append(img_conponent)
        yield event.chain_result(msg_chain)
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
    
    else:
        # 尝试搜索sega新曲列表
        sega_songs = []
        with open(SEGA_SONG_PATH, "r", encoding="utf-8") as f:
            sega_songs = json.load(f)
        title_list = [sega_songs.get('title') for sega_songs in sega_songs]
        searcher = Searcher()
        matched_songs = searcher.generalFuzzySearch(name, title_list)
        
        if len(matched_songs) == 1:
            matched_song = [song for song in sega_songs if song.get('title') == matched_songs[0]][0]
            
            songutil = SongUtil()
            songutil.checkIsHit(Config.SEGA_COVER_URL, matched_song.get('image'))
            
            img = Comp.Image(os.path.join(COVER_CACHE_DIR, matched_song.get('image')))
            yield event.chain_result([
                Comp.Plain(f"新曲 - {matched_song.get('title')}\n"),
                Comp.Plain(f"by {matched_song.get('artist')}\n"),
                Comp.Plain(f"Basic {matched_song.get('lev_bas')}\n"),
                Comp.Plain(f"Advanced {matched_song.get('lev_adv')}\n"),
                Comp.Plain(f"Expert {matched_song.get('lev_exp')}\n"),
                Comp.Plain(f"Master {matched_song.get('lev_mas')}\n"),
                Comp.Plain(f"Ultima {matched_song.get('lev_ult', '-')}" if matched_song.get('lev_ult')!="" else ""),
                img,
            ])
            return
        elif len(matched_songs) > 1:
            return
        else:
            yield event.plain_result("没有找到该歌曲，试着输入歌曲全称或其他别名")