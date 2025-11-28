import os
import json
import random
from PIL import Image

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import astrbot.api.message_components as Comp

from ..config import Config
from .query_song import searchSong
from .utils.songutil import SongUtil
from .utils.guessgame import GuessGame

SONGS_PATH = os.path.join(Config.DATA_PATH, Config.SONG_PATH)
GAME_CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", 'cache', 'others')
COVER_CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache', 'covers')

async def queryGuess(event: AstrMessageEvent, arg: str, pattern: str, guessgame: GuessGame):
    '''处理猜歌事件
    
    Args:
        ctx (EventContext): 事件上下文
        args (list): 参数列表
    Returns:
        None: 无返回值
    '''
    songs = []
    match pattern:
        case "diff":
            '''创建猜歌曲目'''
            difficulty = arg
            group_id = event.get_group_id()
            if not guessgame.check_is_exist(group_id):
                guessgame.add_group(group_id)
                '''为该群创建一个新的猜歌游戏'''
                songs = None
                with open(SONGS_PATH, "r", encoding="utf-8-sig") as file:
                    songs = json.load(file)
                song = random.choice(songs)
                # 过滤World's End曲目
                # while song.get("songId").startswith("(WE)"):
                #     song = random.choice(songs)
                cid = song.get('idx')
                guessgame.set_song_index(group_id, cid)
                
                songutil = SongUtil()
                songutil.checkIsHit(Config.COVER_URL, song.get('img'))
                
                # 随机剪裁曲绘
                difficulty = difficulty if difficulty else "mas"
                factor = 2
                match difficulty:
                    case "bas":
                        factor = 1.5
                    case "adv":
                        factor = 1.8
                    case "exp":
                        factor = 2.2
                    case "mas":
                        factor = 2.5
                    case "ult":
                        factor = 3.0
                    case _:
                        factor = 2.5
                img_path = os.path.join(COVER_CACHE_DIR, song.get('img') + ".webp")
                img = Image.open(img_path)
                img_w, img_h = img.size
                new_w = img_w / factor
                new_h = img_h / factor
                rand_x = random.randint(0, int(img_w - new_w))
                rand_y = random.randint(0, int(img_h - new_h))
                new_img = img.crop((rand_x, rand_y, rand_x + new_w, rand_y + new_h))
                new_img.save(os.path.join(GAME_CACHE_PATH, f"{group_id}.png"))
                
                # 加载剪裁后的曲绘
                img_component = Comp.Image(os.path.join(GAME_CACHE_PATH, f"{group_id}.png"))
                msg_chain = [
                    Comp.Plain(f"Chunithm Guess\n裁剪难度：{difficulty}\n可以使用“guess [歌名/别名]”进行猜歌"),
                    img_component
                ]
                yield event.chain_result(msg_chain)
                
            else:
                '''该群已经有猜歌游戏'''
                yield event.chain_result([
                    Comp.At(qq=event.get_sender_id()),
                    Comp.Plain("\n该群已经有正在进行的猜歌，请不要重复创建")
                ])
                return
        case "end":
            if not guessgame.check_is_exist(event.get_group_id()):
                yield event.chain_result([
                    Comp.At(qq=event.get_sender_id()),
                    Comp.Plain("\n该群还没有创建猜歌，可以使用“chu guess [难度]”进行创建")
                ])
                return
            songs = None
            song = None
            with open(SONGS_PATH, "r", encoding="utf-8-sig") as file:
                songs = json.load(file)
            true_index = guessgame.get_group_index(event.get_group_id())
            for s in songs:
                if s.get('idx') == true_index:
                    song = s
                    break
            songutil = SongUtil()
            songutil.checkIsHit(Config.COVER_URL, song.get('img')) # type: ignore
            img_component = Comp.Image(os.path.join(COVER_CACHE_DIR, song.get('img') + ".webp")) # type: ignore
            yield event.chain_result([
                Comp.Plain(f"好像没人猜出来捏，正确答案为：\nc{true_index} - {song.get('title')}"), # type: ignore
                img_component,
                Comp.Plain(f"可以顺手使用“chuset c{true_index} [别名]”为该歌曲添加别名，方便以后的猜歌")
            ])
            guessgame.remove_group(event.get_group_id())
            yield event.plain_result("已结束此次猜歌\n可使用“chu guess [难度]”创建新的猜歌")
            return
        case "name":
            '''检查猜歌'''
            name = arg
            group_id = event.get_group_id()
            song = None
            cid = -1
            
            if not guessgame.check_is_exist(group_id):
                yield event.chain_result([
                    Comp.At(qq=event.get_sender_id()),
                    Comp.Plain("\n该群还没有创建猜歌，可以使用“chu guess [难度]”进行创建")
                ])
                return
                
            with open(SONGS_PATH, "r", encoding="utf-8-sig") as file:
                songs = json.load(file)
            
            matched_songs = searchSong(name)
            
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
                    name = None
                    for song in songs:
                        if song.get('idx') == cid:
                            name = song.get('title')
                            break
                    msg_chain.append(Comp.Plain(f"c{cid} - {name}\n"))
                msg_chain.append(Comp.Plain(f"\n请使用cid进行精准查询"))
                yield event.chain_result(msg_chain) # type: ignore
                return
            
            '''检查index是否正确'''
            if guessgame.check_is_correct(group_id, cid):
                songutil = SongUtil()
                songutil.checkIsHit(Config.COVER_URL, song.get('img'))
                img_component = Comp.Image(os.path.join(COVER_CACHE_DIR, song.get('img') + ".webp"))
                yield event.chain_result([
                    Comp.At(qq=event.get_sender_id()),
                    Comp.Plain(f"\n恭喜捏，正确答案是：\nc{cid} - {song.get('title')}"),
                    img_component
                ])
                # 移除群的猜歌游戏
                guessgame.remove_group(group_id)
                return
            else:
                yield event.chain_result([Comp.At(qq=event.get_sender_id()), Comp.Plain(f"\n不对捏，再试试吧")])
                return
        case "hint":
            '''获取提示'''
            group_id = event.get_group_id()
            if not guessgame.check_is_exist(group_id):
                yield event.chain_result([
                    Comp.At(qq=event.get_sender_id()),
                    Comp.Plain("\n该群还没有创建猜歌，可以使用“chu guess [难度]”进行创建")
                ])
                return
            cid = guessgame.get_group_index(group_id)
            song = None
            with open(SONGS_PATH, "r", encoding="utf-8-sig") as file:
                songs = json.load(file)
            target_songs = []
            for s in songs:
                if s.get('idx') == cid:
                    target_songs.append(s)
            song = target_songs[0]
            # bpm, category, artist, 定数, notes
            songutil = SongUtil()
            seed = random.randint(0, 3)
            hints = [
                f"歌曲分类为：{song.get('genre')}",
                f"曲师为：{song.get('artist')}",
                f"{songutil.getIndex2Diff(seed)}难度定数为：{target_songs[seed].get('const')}",
                f"{songutil.getIndex2Diff(seed)}难度有{target_songs[seed].get('notes')}个note",
                f"发行版本为：{song.get('version')}",
            ]
            
            hint = random.choice(hints)
            yield event.chain_result([
                Comp.Plain("提示🌟\n"),
                Comp.Plain(hint)
            ])
            return