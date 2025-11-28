import os
import json
import sqlite3

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import astrbot.api.message_components as Comp

from ..main import Config
from .query_song import searchSong
from .utils.songutil import SongUtil

SONGS_PATH = os.path.join(Config.DATA_PATH, Config.SONG_PATH)
DB_PATH = os.path.join(os.path.dirname(__file__), "..", 'data', 'data.db')

def updateScore(user_id: str, cid: str, score: int, difficulty: int, name: str) -> tuple[int, str]:
    '''更新歌曲分数'''
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(f"INSERT OR REPLACE INTO record (user_id, cid, score, difficulty) VALUES (?, ?,?,?)", (user_id, cid, score, difficulty))
        conn.commit()
        conn.close()
        su = SongUtil()
        return 0, f"已将c{cid} - {name}的{su.getIndex2Diff(difficulty)}难度分数更新为{score}"
    except sqlite3.Error as e:
        print(e)
        return -1, f"更新失败：{e}"
    

async def queryUpdScore(event: AstrMessageEvent, score: int, name: str, difficulty: str):
    '''更新歌曲分数
    
    Args:
        ctx (EventContext): 事件上下文
        args (list): 参数列表
    Returns:
        None: 无返回值
    '''
    name = name.strip()
    user_id = event.get_sender_id()
    if difficulty is None:
        difficulty = "mas"

    if difficulty != "exp" and difficulty != "mas" and difficulty != "ult":
        yield event.plain_result("ChunithmUtil:只接受\"exp\",\"mas\",\"uly\"作为难度")
        return
    
    cids = searchSong(name)
    
    songs = []
    with open(SONGS_PATH, 'r', encoding='utf-8-sig') as f:
        songs = json.load(f)
    if len(cids) == 0:
        yield event.plain_result("没有找到该歌曲，试着输入歌曲全称或其他别名")
        return
    elif len(cids) > 1:
        msg_chain = [Comp.Plain(f"有多个曲目符合条件\n")]
        for cid in cids:
            name = None # type: ignore
            for song in songs:
                if song.get('idx') == cid:
                    name = song.get('title')
                    break
            msg_chain.append(Comp.Plain(f"c{cid} - {name}\n"))
        msg_chain.append(Comp.Plain(f"\n请使用cid进行精准查询"))
        yield event.chain_result(msg_chain) # type: ignore
        return
    
    cid = cids[0]
    target_songs = []
    songutil = SongUtil()
    difficulty = songutil.getDiff2Index(difficulty) # type: ignore
    for song in songs:
        if song.get('idx') == cid:
            target_songs.append(song)
    try:
        if difficulty == 4 and len(target_songs) < 5: # 检查是否有Ultima难度
            yield event.plain_result(f"歌曲{song.get('title')}无Ultima难度")
            return
    except Exception as e:
        yield event.plain_result(f"未知难度： {e}")
        return
    # 切换为对应难度
    song = target_songs[difficulty] # type: ignore

    _, msg = updateScore(user_id, cid, score, difficulty, song.get('title')) # type: ignore
    msg_chain = [Comp.Plain(f"{msg}")]
    yield event.chain_result(msg_chain) # type: ignore
    