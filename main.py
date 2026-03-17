import asyncio
import aiohttp

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger


class AncientPoem(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 惰性初始化 session，不在 __init__ 中创建
        self.session = None

    async def _get_session(self):
        '''获取或创建 session'''
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def terminate(self):
        '''插件卸载时清理资源'''
        if self.session and not self.session.closed:
            await self.session.close()

    @filter.command("gs")
    async def get_poem(self, event: AstrMessageEvent, count: int = 1):
        '''随机获取古诗，可指定数量 (默认为1，最大为5)
        
        Args:
            count (int): 获取古诗的数量
        '''
        
        # 参数类型安全检查
        try:
            count = int(count)
        except (ValueError, TypeError):
            count = 1
            
        # 限制数量，防止滥用
        if count > 5:
            count = 5
        elif count < 1:
            count = 1
            
        url = "https://v1.hitokoto.cn/?c=i"
        
        # 记录本次已发送的诗句，用于去重
        sent_contents = set()
        success_count = 0
        
        # 增加最大重试次数，避免无限循环卡死
        max_attempts = max(count * 5, 20)
        attempts = 0

        try:
            session = await self._get_session()
            
            # 循环直到成功发送指定数量的诗句，或达到最大尝试次数
            while success_count < count and attempts < max_attempts:
                attempts += 1
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
                
                except asyncio.CancelledError:
                    raise  # 显式放行取消信号
                    
                except Exception as e:
                    logger.exception(f"单次获取古诗失败: {e}")  # 记录完整堆栈
                    # 发生异常时也等待一下，避免死循环报错刷屏
                    await asyncio.sleep(1)
                    continue
            
            if success_count < count:
                logger.warning(f"未完全满足请求数量: 请求 {count}, 实际 {success_count}, 尝试 {attempts}")
                if success_count == 0:
                     yield event.plain_result("获取古诗失败，请稍后再试。")
                else:
                     yield event.plain_result(f"已尝试 {attempts} 次，成功获取 {success_count} 首，部分获取失败。")

        except asyncio.CancelledError:
            raise
            
        except Exception as e:
            logger.exception(f"获取古诗任务失败: {e}")
            yield event.plain_result("获取古诗失败，请稍后再试。")
