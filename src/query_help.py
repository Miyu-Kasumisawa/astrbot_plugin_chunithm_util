from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp


async def queryHelp(event: AstrMessageEvent):
    '''获取帮助信息
    
    Args:
        event (AstrMessageEvent): 事件上下文
    Returns:
        None
    '''
    yield event.chain_result([
        Comp.Plain("CHUNITHM UTILS 指令帮助：\n"),
        Comp.Plain("暂不支持私聊\n"),
        Comp.Plain("· chu help - 查看帮助\n"),
        Comp.Plain("· [别名/cid]是什么歌 - 查找歌曲\n"),
        Comp.Plain("· 添加别名|chuset [歌曲cid] [别名1，别名2，...] - 为歌曲添加别名\n"),
        Comp.Plain("· 别名|alias [歌曲cid] - 查看指定歌曲所有别名\n"),
        Comp.Plain("· chu随机一曲|chu随机 - 随机一首歌\n"),
        Comp.Plain("· chu lv [定数] - 查看指定定数所有歌曲\n"), 
        Comp.Plain("· chu容错 [歌曲cid/别名] [难度] - 容错计算\n"),
        Comp.Plain("· chuchart [歌曲cid/别名] [难度] - 查看谱面\n"),
        Comp.Plain("· chu曲师 [曲师名] - 查看曲师作品\n"),
        # Plain("· chu谱师 [谱师名] - 查看谱师谱面\n"),
        Comp.Plain("· chu bind [服务器] [TOKEN] - 绑定服务器\n"),
        Comp.Plain("· chu copy [服务器] - 迁移游玩数据\n"),
        Comp.Plain("· b30 [simple/-] - b30查询|默认simple\n"),
        Comp.Plain("· chu update - 更新曲目、谱面信息\n"),
        Comp.Plain("· chu guess [难度] - 创建猜歌游戏\n"),
        Comp.Plain("· chu guess end - 结束当前猜歌游戏\n"),
        Comp.Plain("· chu hint - 请求猜歌提示\n"),
        Comp.Plain("· guess [歌曲名] - 猜歌\n"),
    ])