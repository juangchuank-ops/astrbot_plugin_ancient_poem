import asyncio
import aiohttp
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger

class AncientPoem(Star):
    def __init__(self, context: Context):
        super().__init__(context)
    
    @filter.command("gs")
    async def get_poem(self, event: AstrMessageEvent, count: int = 1):
        '''随机获取古诗，可指定数量 (默认为1，最大为5)
        
        Args:
            count (int): 获取古诗的数量
        '''
        
        # 限制数量，防止滥用
        if count > 5:
            count = 5
        elif count < 1:
            count = 1
            
        url = "https://v1.hitokoto.cn/?c=i"
        
        # 记录本次已发送的诗句，用于去重
        sent_contents = set()
        success_count = 0

        try:
            async with aiohttp.ClientSession() as session:
                # 循环直到成功发送指定数量的诗句
                while success_count < count:
                    try:
                        # 增加短暂延时，避免触发 API 速率限制
                        await asyncio.sleep(0.2)
                        
                        async with session.get(url, timeout=10) as resp:
                            if resp.status != 200:
                                logger.warning(f"获取古诗失败，HTTP状态码: {resp.status}")
                                # 如果 API 报错，稍微多等待一下
                                await asyncio.sleep(1)
                                continue
                            
                            data = await resp.json()
                            
                            content = data.get("hitokoto", "未知诗句")
                            
                            # 去重检查
                            if content in sent_contents:
                                logger.info(f"跳过重复诗句: {content}")
                                continue
                                
                            sent_contents.add(content)
                            success_count += 1
                            
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
                        logger.error(f"单次获取古诗失败: {e}")
                        # 发生异常时也等待一下，避免死循环报错刷屏
                        await asyncio.sleep(1)
                        continue
                        
                if success_count == 0:
                     yield event.plain_result("获取古诗失败，请稍后再试。")

        except Exception as e:
            logger.error(f"获取古诗任务失败: {e}")
            yield event.plain_result("获取古诗失败，请稍后再试。")
