import re
import os
import shutil
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import astrbot.api.message_components as Comp

from .src.query_help import *
from .src.query_song import *
from .src.query_chart import *
from .src.query_alias import *
from .src.query_rdnsong import *
from .src.query_tolerance import * 
from .src.query_aritst import *
# from .src.query_notedesigner import *
from .src.query_level import *
from .src.query_update import *
from .src.query_guess import *
from .src.query_method import *
# from .src.query_chart_we import * 疑似旧版本残留，替换为未使用但数据结构匹配的另一文件
from .src.query_wechart import *
from .src.query_updscore import *
from .src.query_querybest import *
from .src.query_copy import *
from .src.query_bind import *

from .src.utils.argsparser import *
from .src.utils.guessgame import *

from .config import Config

os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("all_proxy", None)
os.environ.pop("ALL_PROXY", None)

#模糊搜索音乐自定义筛选函数
class MusicSearchFilter(filter.CustomFilter):
    def filter(self ,event:AstrMessageEvent, cfg: AstrBotConfig) -> bool:
        if (re.match(r"^(.+)是什么歌$",event.message_str)):
            return True
        else:
            return False

# 注册插件
@register("ChunithmUtil", "Amethyst", "集成多项Chunithm实用功能的AstrBot插件🧩", "1.1")
class ChunithmUtilPlugin(Star):
    # 插件加载时触发
    def __init__(self, context: Context):
        #初始化配置
        Config.update_from_dict(self.context.get_config().values())
        #检查内置别名列表是否复制到数据路径&检查数据目录是否存在
        if not os.path.exists(os.path.join(Config.DATA_PATH,Config.ALIAS_PATH)):
            if not os.path.exists(os.path.join(Config.DATA_PATH,"data")):
                os.makedirs(os.path.join(Config.DATA_PATH,"data"))
            shutil.copy2(os.path.join(os.path.dirname(__file__),'data','alias.json'),os.path.join(Config.DATA_PATH,Config.ALIAS_PATH))
        """
        self.instructions = {
            "chu help": 
                r"^chu\s?help$",
            # ===== 查歌 =====
            "[歌名]是什么歌": 
                r"^(.+)是什么歌$",
            "chu随机一曲": 
                r"^chu随机[一曲]*$",
            "添加别名|chuset [歌曲id] [别名1],[别名2],...": 
                r"(?:^添加别名|chuset) (c\d+)\s+((?:[^,，]+[,，]?)+)$",
            "别名[歌曲id|歌曲别名]": 
                r"^别名\s*(.+)$",
            "chu lv [难度]": 
                r"^chu\s?lv\s?(\S+)$",
            "chu容错 [歌曲id/别名] [难度]": 
                r"^(?:chu容错|churc)\s?(c\d+|.+?)(?: (exp|mas|ult))?$",
            # ===== 查谱 =====
            "chuchart [歌曲id/别名] [难度]": 
                r"^chuchart\s?(c\d+|.+?)(?: (exp|mas|ult))?$",
            "wechart [歌曲id/别名] [难度]":
                r"^wechart\s?(c\d+|.+?)(.*)$",
            # ===== 查人 =====
            "chu曲师 [曲师名]" : 
                r"^chu(?:曲师|\s?qs)\s?(.+)$",
            # "chu谱师 [谱师名]": 
            #     r"^chu(?:谱师|\s?ps)\s?(.+)$",
            "chu update":
                r"^chu\s?update$",
            # ===== 猜歌 =====
            "chu guess [难度]":
                r"^chu\s?guess(?: (bas|adv|exp|mas|ult))?$",
            "chu guess end":
                r"^(chu\s?guess\s?end|cge)$",
            "guess [歌名]":
                r"^guess\s?(.+)$",
            "chu hint":
                r"^chu\s?hint$",
            # ===== 查分 =====
            "update [分数] [歌名] [难度]":
                 r"upd\s*(\d+)\s*(.*?)(?:\s+(exp|mas|ult))?$",
            "b30":
                r"^b30(?:\s?(simple))?$",
            "b50":
                r"^b50(?:\s?(simple))?$",
            "chu copy [服务器]":
                r"^chu\s?copy\s?(\S+)$",
            "chu bind [服务器] [TOKEN]":
                r"^chu\s*bind\s+(\S+)\s+(\S+)$",
            # ===== 弃用 =====
            "[歌名]这里怎么打":
                r"^(.+)这里怎么打$",
            "[歌名]有什么手法":
                r"^(.+)有什么手法$",
            "[歌名]的[mid]这么打":
                r"^(.+)的(\S+)这么打$",
        }
        """
        self.guessgame = GuessGame()
    """
    def matchPattern(self, msg) -> str:
        '''匹配指令
        
        Args:
            msg: 指令内容
        Returns:
            匹配结果
        '''
        res = None
        for pattern in self.instructions:
            if re.match(self.instructions[pattern], msg):
                res = pattern
        return res
    """
    # 异步初始化
    async def initialize(self):
        pass
    
    #chu指令组
    @filter.command_group('chu')
    def chu(self):
        pass

    #帮助
    @chu.command("help")
    async def chuhelp(self, event:AstrMessageEvent):
        queryHelp(event)

    #根据定数筛选
    @chu.command("lv")
    async def chulv(self, event:AstrMessageEvent, level:str):
        await queryLevel(event, level)

    #更新数据
    @chu.command("update")
    async def chuupdate(self, event:AstrMessageEvent):
        queryUpdate(event)

    #猜歌管理
    @chu.command("guess")
    async def chuguess(self, event:AstrMessageEvent, arg:str):
        if arg == "bas" or arg == "adv" or arg == "exp" or arg == "mas" or arg == "ult":
            queryGuess(event, arg, "diff", self.guessgame)
        elif arg == "end":
            queryGuess(event, arg, "end", self.guessgame)

    #猜歌提示
    @chu.command("hint")
    async def chuhint(self, event:AstrMessageEvent):
        queryGuess(event, "", "hint", self.guessgame)

    #迁移游玩数据
    @chu.command("copy")
    async def chucopy(self, event:AstrMessageEvent, server:str):
        queryCopy(event,server)

    #迁移游玩数据
    @chu.command("bind")
    async def chubind(self, event:AstrMessageEvent, server:str, token:str):
        queryBind(event,server,token)


    #猜歌
    @filter.command("guess")
    async def guess(self, event:AstrMessageEvent, arg:str):
        queryGuess(event, arg, "name", self.guessgame)

    
    

    #模糊搜索音乐
    @filter.custom_filter(MusicSearchFilter)
    async def MusicSearch(self, event:AstrMessageEvent):
        match = re.search(r"^(.+)是什么歌$", event.message_str)
        if (match == None):
            yield event.plain_result("ChunithmUtil:查询条件不能为空")
        else:
            querySong(event, match.group(1))

    #随机音乐
    @filter.command("chu随机一曲",alias={"chu随机"})
    async def RandomMusic(self, event:AstrMessageEvent):
        queryRdnSong(event)
        
    #添加别名
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @filter.command("chuset",alias={"添加别名"})
    async def AddAlias(self, event:AstrMessageEvent, cid:str, alias:str):
        queryAddAlias(event, cid, alias)

    #查询别名
    @filter.command("alias",alias={"别名"})
    async def GetAlias(self, event:AstrMessageEvent, condition:str):
        queryGetAlias(event, condition)

    #查询容错
    @filter.command("churc",alias={"chu容错"})
    async def Tolerance(self, event:AstrMessageEvent, name:str, difficulty:str):
        queryTolerance(event, name, difficulty)

    #查询谱面
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @filter.command("chuchart")
    async def ChuChart(self, event:AstrMessageEvent, name:str, difficulty:str):
        queryChart(event, name, difficulty)

    #查询WE谱面
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    @filter.command("wechart")
    async def WeChart(self, event:AstrMessageEvent, name:str, type:str):
        queryChartWE(event, name, type)

    #查询曲师
    @filter.command("chuqs",alias={"chu曲师"})
    async def ChuArtist(self, event:AstrMessageEvent, artist:str):
        queryArtist(event, artist)

    #更新分数
    @filter.command("update")
    async def UpdateScore(self, event:AstrMessageEvent, score: int, name: str, difficulty: str):
        queryUpdScore(event, score, name, difficulty)

    #b30
    @filter.command("b30")
    async def b30(self, event:AstrMessageEvent, arg:str):
        queryQueryBest(event, arg, "30")

    #b50
    @filter.command("b50")
    async def b50(self, event:AstrMessageEvent, arg:str):
        queryQueryBest(event, arg, "50")

    """
    @handler(GroupMessageReceived)
    async def msg_received(self, ctx: EventContext):
        msg = str(ctx.event.message_chain).strip()
        pattern = self.matchPattern(msg)
        if not pattern:
            return
        match pattern:
            case "[歌名]是什么歌":
                await querySong(ctx, parseArgs(self.instructions[pattern], msg))
            
            case "chu随机一曲":
                await queryRdnSong(ctx, parseArgs(self.instructions[pattern], msg))
            
            case "添加别名|chuset [歌曲id] [别名1],[别名2],...":
                await queryAddAlias(ctx, parseArgs(self.instructions[pattern], msg))
            
            case "别名[歌曲id|歌曲别名]":
                await queryGetAlias(ctx, parseArgs(self.instructions[pattern], msg))
            
            case "chu lv [难度]":
                await queryLevel(ctx, parseArgs(self.instructions[pattern], msg))
            
            case "chu容错 [歌曲id/别名] [难度]":
                await queryTolerance(ctx, parseArgs(self.instructions[pattern], msg))
            
            case "chuchart [歌曲id/别名] [难度]":
                await queryChart(ctx, parseArgs(self.instructions[pattern], msg))
                
            case "wechart [歌曲id/别名] [难度]":
                await queryChartWE(ctx, parseArgs(self.instructions[pattern], msg))
            
            case "chu曲师 [曲师名]":
                await queryArtist(ctx, parseArgs(self.instructions[pattern], msg))
                
            # case "chu谱师 [谱师名]":
            #     await queryNoteDesigner(ctx, parseArgs(self.instructions[pattern], msg))
            
            case "chu update":
                await queryUpdate(ctx, parseArgs(self.instructions[pattern], msg))
            
            case "chu help":
                await queryHelp(ctx)
            
            case "chu guess [难度]" | "chu guess end" | "guess [歌名]" | "chu hint":
                await queryGuess(ctx, parseArgs(self.instructions[pattern], msg), pattern, self.guessgame)
                
            case "update [分数] [歌名] [难度]":
                await queryUpdScore(ctx, parseArgs(self.instructions[pattern], msg))
            
            case "b30" | "b50":
                await queryQueryBest(ctx, parseArgs(self.instructions[pattern], msg), pattern=pattern)
            
            case "chu copy [服务器]":
                await queryCopy(ctx, parseArgs(self.instructions[pattern], msg))
            
            case "chu bind [服务器] [TOKEN]":
                await queryBind(ctx, parseArgs(self.instructions[pattern], msg))
            # case "[歌名]这里怎么打" | "[歌名]有什么手法" | "[歌名]的[mid]这么打":
            #     await queryMethod(ctx, parseArgs(self.instructions[pattern], msg), pattern, msg)
            
            case _:
                pass
        """
                        
    # 插件卸载时触发
    def __del__(self):
        pass
