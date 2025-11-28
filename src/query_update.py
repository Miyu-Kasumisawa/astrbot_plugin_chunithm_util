import os
import subprocess

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import astrbot.api.message_components as Comp

from ..main import Config
from .utils import songmeta

SCRIPT_SONGMETA_PATH = os.path.join(os.path.dirname(__file__), "utils", "songmeta.py")
SCRIPT_MAPPING_PATH = os.path.join(os.path.dirname(__file__), "utils", "mapping.py")

async def queryUpdate(event: AstrMessageEvent):
    
    diff = None
    try:
        yield event.plain_result("正在更新...")
        diff = songmeta.songMeta() #待修复
        subprocess.run(['python', SCRIPT_MAPPING_PATH])
        msg_chain =[
            Comp.Plain("更新成功"),
        ]
        
        if len(diff) > 20:
            msg_chain.append(Comp.Plain(f"，新增曲目过多，仅展示前20首"))
        if len(diff) != 0:
            msg_chain.append(Comp.Plain(f"，新增曲目：\n"))
            for song in diff[::-1][ : min(20, len(diff))]:
                msg_chain.append(Comp.Plain(f"· {song.get('songId')}\n"))
        yield event.chain_result(msg_chain) # type: ignore
    
    except subprocess.CalledProcessError as e:
        yield event.plain_result(f"更新失败：{e}")
        return