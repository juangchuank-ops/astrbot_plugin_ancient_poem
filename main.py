import aiohttp
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star

class AncientPoem(Star):
    def __init__(self, context: Context):
        super().__init__(context)
    
    @filter.command("gs")
    async def get_poem(self, event: AstrMessageEvent):
        '''随机获取一句古诗'''
        
        # 使用 Hitokoto API 获取诗词
        # c=i 表示获取诗词
        url = "https://v1.hitokoto.cn/?c=i"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status != 200:
                        yield event.plain_result(f"获取古诗失败，HTTP状态码: {resp.status}")
                        return
                    
                    data = await resp.json()
                    
                    # 解析返回的数据
                    # Hitokoto 格式:
                    # {
                    #   "hitokoto": "诗句内容",
                    #   "from": "出处",
                    #   "from_who": "作者",
                    #   ...
                    # }
                    
                    content = data.get("hitokoto", "未知诗句")
                    origin = data.get("from", "未知出处")
                    author = data.get("from_who")
                    
                    # 构建回复文本
                    reply_text = f"「{content}」\n"
                    if author:
                        reply_text += f"—— {author}《{origin}》"
                    else:
                        reply_text += f"—— 《{origin}》"
                        
                    yield event.plain_result(reply_text)
                    
        except Exception as e:
            self.context.logger.error(f"获取古诗失败: {e}")
            yield event.plain_result("获取古诗失败，请稍后再试。")
