"""
UserBot 爬虫模块
使用 Telethon 爬取频道内容
⚠️ 需要 API ID/Hash，默认禁用，通过开关控制
"""
import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Optional
from telethon import TelegramClient, events, functions
from telethon.tl.types import Channel, Chat
from telethon.errors import FloodWaitError, ChannelPrivateError, UsernameNotOccupiedError

from config import config
from database import db
import logging

logger = logging.getLogger(__name__)


class ChannelCrawler:
    """频道爬虫类"""
    
    def __init__(self):
        self.client: Optional[TelegramClient] = None
        self.is_running = False
        self.enabled = False
        self.joined_today = 0
        self.last_join_date = None
    
    async def initialize(self) -> bool:
        """初始化 UserBot 客户端"""
        # 检查配置
        if not config.API_ID or not config.API_HASH:
            logger.error("❌ UserBot 配置不完整：缺少 API_ID 或 API_HASH")
            return False
        
        try:
            self.client = TelegramClient(
                config.SESSION_NAME,
                config.API_ID,
                config.API_HASH
            )
            
            await self.client.start(phone=config.PHONE_NUMBER)
            
            # 验证登录
            me = await self.client.get_me()
            logger.info(f"✅ UserBot 已登录: {me.first_name} (@{me.username})")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ UserBot 初始化失败: {e}")
            return False
    
    async def start(self):
        """启动爬虫"""
        # 检查开关
        crawler_enabled = await db.get_crawler_status()
        if not crawler_enabled:
            logger.info("⏸️ 爬虫未启用（数据库开关为 false）")
            return
        
        if not await self.initialize():
            logger.error("❌ 爬虫启动失败：初始化失败")
            return
        
        self.enabled = True
        self.is_running = True
        
        logger.info("🚀 爬虫已启动")
        
        # 注册事件处理器
        @self.client.on(events.NewMessage)
        async def handle_new_message(event):
            await self._process_new_message(event)
        
        # 开始监听
        logger.info("👂 开始监听频道消息...")
        
        # 周期性任务
        asyncio.create_task(self._periodic_join_channels())
        asyncio.create_task(self._periodic_health_check())
        
        # 保持运行
        await self.client.run_until_disconnected()
    
    async def stop(self):
        """停止爬虫"""
        self.is_running = False
        self.enabled = False
        
        if self.client:
            await self.client.disconnect()
        
        logger.info("⏹️ 爬虫已停止")
    
    async def _process_new_message(self, event):
        """处理新消息"""
        try:
            message = event.message
            
            # 获取频道信息
            chat = await event.get_chat()
            if not isinstance(chat, Channel):
                return  # 只处理频道消息
            
            # 检查频道是否在数据库中
            channel = await db.get_channel_by_username(chat.username)
            if not channel:
                logger.debug(f"跳过未知频道: @{chat.username}")
                return
            
            # 提取消息内容
            content = message.text or ""
            media_type = self._get_media_type(message)
            
            # 转发到私有存储频道（如果配置了）
            storage_message_id = None
            if config.STORAGE_CHANNEL_ID:
                try:
                    forwarded = await self.client.forward_messages(
                        config.STORAGE_CHANNEL_ID,
                        message
                    )
                    storage_message_id = str(forwarded.id)
                except Exception as e:
                    logger.error(f"转发消息失败: {e}")
            
            # 存入数据库
            await db.add_message(
                channel_id=channel['id'],
                message_id=str(message.id),
                content=content,
                media_type=media_type,
                publish_date=message.date,
                storage_message_id=storage_message_id
            )
            
            logger.debug(f"✅ 已索引消息: @{chat.username} - {message.id}")
            
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
    
    async def _periodic_join_channels(self):
        """周期性加入新频道"""
        while self.is_running:
            try:
                # 重置每日计数
                today = datetime.now().date()
                if self.last_join_date != today:
                    self.joined_today = 0
                    self.last_join_date = today
                
                # 检查是否达到每日限制
                if self.joined_today >= config.MAX_CHANNELS_PER_DAY:
                    logger.info(f"⏸️ 今日加入频道数已达上限: {self.joined_today}")
                    await asyncio.sleep(3600)  # 等待1小时后再检查
                    continue
                
                # 获取待加入的频道
                channels = await db.get_all_channels(status='pending', limit=5)
                
                for channel in channels:
                    if not self.is_running:
                        break
                    
                    username = channel['channel_username']
                    
                    try:
                        # 尝试加入频道
                        success = await self._join_channel(username)
                        
                        if success:
                            # 更新数据库状态
                            await db.update_channel(
                                channel['id'],
                                status='active',
                                is_verified=True,
                                last_crawled=datetime.now()
                            )
                            
                            self.joined_today += 1
                            logger.info(f"✅ 已加入频道: @{username} (今日第 {self.joined_today} 个)")
                            
                            # 随机延迟（避免被检测）
                            delay = random.randint(
                                config.CRAWL_DELAY_MIN,
                                config.CRAWL_DELAY_MAX
                            )
                            await asyncio.sleep(delay)
                        else:
                            # 标记为失败
                            await db.update_channel(
                                channel['id'],
                                status='failed'
                            )
                    
                    except Exception as e:
                        logger.error(f"加入频道失败 @{username}: {e}")
                        await db.update_channel(
                            channel['id'],
                            status='failed',
                            notes=str(e)[:200]
                        )
                
                # 等待一段时间后继续
                await asyncio.sleep(1800)  # 30分钟
                
            except Exception as e:
                logger.error(f"周期性加入频道任务出错: {e}")
                await asyncio.sleep(300)  # 5分钟后重试
    
    async def _join_channel(self, username: str) -> bool:
        """加入频道"""
        try:
            # 移除 @ 符号
            username = username.lstrip('@')
            
            # 获取实体
            entity = await self.client.get_entity(username)
            
            # 检查是否已加入
            if isinstance(entity, Channel):
                # 尝试加入
                await self.client(functions.channels.JoinChannelRequest(entity))
                return True
            
            return False
            
        except UsernameNotOccupiedError:
            logger.warning(f"频道不存在: @{username}")
            return False
        except ChannelPrivateError:
            logger.warning(f"频道为私有: @{username}")
            return False
        except FloodWaitError as e:
            logger.warning(f"触发限流，需等待 {e.seconds} 秒")
            await asyncio.sleep(e.seconds)
            return False
        except Exception as e:
            logger.error(f"加入频道失败 @{username}: {e}")
            return False
    
    async def _periodic_health_check(self):
        """周期性健康检查"""
        while self.is_running:
            try:
                # 检查客户端连接
                if self.client and self.client.is_connected():
                    logger.debug("✅ UserBot 连接正常")
                else:
                    logger.warning("⚠️ UserBot 连接断开，尝试重连...")
                    await self.initialize()
                
                # 检查数据库开关
                crawler_enabled = await db.get_crawler_status()
                if not crawler_enabled and self.enabled:
                    logger.info("⏸️ 检测到爬虫被禁用，停止爬虫...")
                    await self.stop()
                    break
                
                await asyncio.sleep(300)  # 5分钟检查一次
                
            except Exception as e:
                logger.error(f"健康检查出错: {e}")
                await asyncio.sleep(60)
    
    def _get_media_type(self, message) -> str:
        """获取消息的媒体类型"""
        if message.photo:
            return 'photo'
        elif message.video:
            return 'video'
        elif message.document:
            return 'document'
        elif message.audio:
            return 'audio'
        elif message.voice:
            return 'voice'
        elif message.sticker:
            return 'sticker'
        elif message.animation:
            return 'animation'
        else:
            return 'text'
    
    async def crawl_history(
        self,
        username: str,
        limit: int = 100
    ) -> int:
        """爬取频道历史消息"""
        if not self.client:
            logger.error("UserBot 未初始化")
            return 0
        
        try:
            username = username.lstrip('@')
            entity = await self.client.get_entity(username)
            
            # 获取频道信息
            channel = await db.get_channel_by_username(username)
            if not channel:
                logger.error(f"数据库中不存在频道: @{username}")
                return 0
            
            count = 0
            async for message in self.client.iter_messages(entity, limit=limit):
                if not message.text and not message.media:
                    continue
                
                content = message.text or ""
                media_type = self._get_media_type(message)
                
                # 转发到存储频道
                storage_message_id = None
                if config.STORAGE_CHANNEL_ID:
                    try:
                        forwarded = await self.client.forward_messages(
                            config.STORAGE_CHANNEL_ID,
                            message
                        )
                        storage_message_id = str(forwarded.id)
                    except:
                        pass
                
                # 存入数据库
                await db.add_message(
                    channel_id=channel['id'],
                    message_id=str(message.id),
                    content=content,
                    media_type=media_type,
                    publish_date=message.date,
                    storage_message_id=storage_message_id
                )
                
                count += 1
                
                # 限速
                if count % 10 == 0:
                    await asyncio.sleep(1)
            
            logger.info(f"✅ 已爬取 @{username} 的 {count} 条历史消息")
            return count
            
        except Exception as e:
            logger.error(f"爬取历史消息失败 @{username}: {e}")
            return 0


# 创建全局爬虫实例
crawler = ChannelCrawler()

