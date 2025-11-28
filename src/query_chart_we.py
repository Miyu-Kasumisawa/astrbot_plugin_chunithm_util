#某些函数不存在，经比对，怀疑该文件为旧版本残留文件，故弃用，换用另一含同名函数的文件
"""
import os
import json
import asyncio

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import astrbot.api.message_components as Comp

from ..main import Config
from .query_song import searchSong
from .utils.wechartutil import WEChartUtil

SONGS_PATH = os.path.join(Config.DATA_PATH, Config.SONG_PATH)
CHART_CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache', 'charts')

async def queryChartWE(event: AstrMessageEvent, name: str, type: str):
    '''查询谱面
    
    
    Args:
        event (AstrMessageEvent): 事件上下文
        name (str): 歌曲名/歌曲cid
        difficulty (str): 歌曲难度
    Returns:
        None: 无返回值
    '''
    songs = []
    song = {}
    
    with open(SONGS_PATH, "r", encoding="utf-8-sig") as file:
        songs = json.load(file)
    
    matched_songs = searchSong(name)
    
    if len(matched_songs) == 1:
        song = [song for song in songs if song.get('songId') == matched_songs[0]][0]
        song_index = songs.index(song)
    elif len(matched_songs) == 0:
        yield event.plain_result(f"没有找到{name}，请尝试输入歌曲全称或其他别名")
        return
    else:
        msg_chain = [Comp.Plain(f"有多个曲目符合条件\n")]
        for songId in matched_songs:
            song_index = songs.index([song for song in songs if song.get('songId') == songId][0])
            msg_chain.append(Comp.Plain(f"c{song_index} - {songId}\n"))
        msg_chain.append(Comp.Plain(f"\n请使用“chuchart [cid]”进行谱面查询"))
        yield event.chain_result(msg_chain) # type: ignore
        return

    '''
    "/chunithm/end/01127end.htm": "/chunithm/chfiles/chlv/star_haya3.png",
    '''

    chartutil = WEChartUtil()
    chartid = chartutil.getChartID(song)
    we_diff = chartutil.getWEDifficulty(chartid, type)
    if chartid == None:
        yield event.plain_result(f"未找到歌曲对应谱面，可能是内部错误或数据未更新")
        return
    if we_diff == None:
        yield event.plain_result(f"未找到歌曲对应难度类型：{type}，可能是内部错误或数据未更新")
        return
    if chartutil.checkIsHit(chartid, type):
        local_path = os.path.join(CHART_CACHE_DIR, f"{chartid}_{type if type else ''}.png")
        try:
            img_conponent = Comp.Image(local_path)
        except FileNotFoundError:
            yield event.plain_result(f"未找到歌曲对应谱面，可能是内部错误或数据未更新")
            return
        yield event.chain_result([
            Comp.Plain(f"歌曲 - {song.get('songId')}\n"),
            Comp.Plain(f"类型 - {type if type else ''}\n"),
            Comp.Plain(f"Artist - {song.get('artist')}\n"),
            img_conponent
        ])
        return
    else:
        print("[ChunithmUtil] 缓存未命中，开始请求")
        asyncio.create_task(chartutil.getChart(chartid, type, event.get_group_id(), song))
"""