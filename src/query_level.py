import os
import json

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import astrbot.api.message_components as Comp

from ..config import Config
from .utils.apicaller import *

SONGS_PATH = os.path.join(Config.DATA_PATH, Config.SONG_PATH)

async def queryLevel(event: AstrMessageEvent, level: str):
    '''查询指定定数的歌曲
    
    Args:
        event (AstrMessageEvent): 事件上下文
        level (str): 难度
    Returns:
        None: 无返回值
    '''

    songs = []
    matched_songs = []
    
    msgs = "歌曲列表：\n"
    
    with open(SONGS_PATH, "r", encoding="utf-8-sig") as file:
        songs = json.load(file)  
    
    if '+' in level:  # +范围
        target_diff = level.split('+')[0]
        for song in songs:
            if int(target_diff) + 0.5 <= song.get('const') < int(target_diff) + 1:
                matched_songs.append({
                    "id":song.get("idx"),
                    "title":song.get('title'),
                    "internalLevelValue":song.get('const')
                })
    elif '.' in level: # 具体定数
        target_diff = float(level)
        for song in songs:
            if target_diff == song.get('const'):
                matched_songs.append({
                    "id":song.get("idx"),
                    "title":song.get('title'),
                    "internalLevelValue":song.get('const')
                })
    else: # x~x+1定数范围
        target_diff = int(level)
        for song in songs:
            if int(target_diff) <= song.get('const') < int(target_diff) + 1:
                matched_songs.append({
                    "id":song.get("idx"),
                    "title":song.get('title'),
                    "internalLevelValue":song.get('const')
                })
    
    matched_songs.sort(key=lambda x:x.get('internalLevelValue'))
    for matched_song in matched_songs:
        msgs = msgs + f"c{matched_song.get('id')} - {matched_song.get('title')} - {matched_song.get('internalLevelValue')}\n"
    
    message_data = {
        "group_id": event.get_group_id,
        "user_id": "",
        "messages": [
            {
                "type": "node",
                "data": {
                    "user_id": "114514",
                    "nickname": "BOT",
                    "content": [
                        {
                            "type": "text",
                            "data": {
                                "text": f"{msgs}"
                            }
                        }
                    ]
                }
            }
        ],
        "news": [
            {"text": f"波师：国服追上日服进度了"},
            {"text": f"波师：[图片]"},
            {"text": f"波师：居然还换了120hz框"}
        ],
        "prompt": "[文件]年度学习资料.zip",
        "summary": "点击浏览",
        "source": "定数表"
    }
    msgplatform = MsgPlatform(3000)
    await msgplatform.callApi("/send_forward_msg", message_data)