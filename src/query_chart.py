import os
import json
import asyncio

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import astrbot.api.message_components as Comp

from ..config import Config
from .query_song import searchSong
from .utils.songutil import SongUtil
from .utils.chartutil import ChartUtil

SONGS_PATH = os.path.join(Config.DATA_PATH, Config.SONG_PATH)
CHART_CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache', 'charts')

async def queryChart(event: AstrMessageEvent, name: str, difficulty: str):
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
    
    if difficulty == None:
        difficulty = "mas"
    
    if difficulty != "exp" and difficulty != "mas" and difficulty != "ult":
        yield event.plain_result("ChunithmUtil:只接受\"exp\",\"mas\",\"uly\"作为难度")
        return

    matched_songs = searchSong(name)
    target_songs = []
    cid = None
    if len(matched_songs) == 1:
        target_songs = [song for song in songs if song.get('idx') == matched_songs[0]]
        song = target_songs[0]
        cid = song.get('idx')
    elif len(matched_songs) == 0:
        yield event.plain_result(f"没有找到{name}，请尝试输入歌曲全称或其他别名")
        return
    else:
        msg_chain = [Comp.Plain(f"有多个曲目符合条件\n")]
        for cid in matched_songs:
            name = None # type: ignore
            for song in songs:
                if song.get('idx') == cid:
                    name = song.get('title')
                    break
            msg_chain.append(Comp.Plain(f"c{cid} - {name}\n"))
        msg_chain.append(Comp.Plain(f"\n请使用cid进行精准查询"))
        yield event.chain_result(msg_chain) # type: ignore
        return
    
    songutil = SongUtil()
    index = songutil.getDiff2Index(difficulty)
    try:
        if index == 4 and len(target_songs) < 5: # 检查是否有Ultima难度
            yield event.plain_result(f"歌曲{song.get('title')}无Ultima难度")
            return
    except Exception as e:
        yield event.plain_result(f"未知难度")
        return
    # 切换为对应难度
    song = target_songs[index]

    chartutil = ChartUtil()
    chartid = chartutil.getChartID(song)
    if chartid == None:
        yield event.plain_result(f"未找到歌曲对应谱面，可能是内部错误或数据未更新")
        return
    if chartutil.checkIsHit(chartid, difficulty):
        local_path = os.path.join(CHART_CACHE_DIR, f"{chartid}_{'' if difficulty == 'mas' else difficulty}.png")
        try:
            img_conponent = Comp.Image(local_path)
        except FileNotFoundError:
            yield event.plain_result(f"未找到歌曲对应谱面，可能是内部错误或数据未更新")
            return
        yield event.chain_result([
            Comp.Plain(f"c{cid} - {song.get('title')}\n"),
            Comp.Plain(f"难度 - {difficulty}\n"),
            Comp.Plain(f"Artist - {song.get('artist')}\n"),
            Comp.Plain(f"BPM - {song.get('bpm')}\n"),
            Comp.Plain(f"Notes - {song.get('notes')}"),
            img_conponent
        ])
        return
    else:
        print("[ChunithmUtil] 缓存未命中，开始请求")
        asyncio.create_task(chartutil.getChart(chartid, difficulty, event.get_group_id(), song))