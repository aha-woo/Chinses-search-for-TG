"""
Bot 主程序
处理用户交互、命令和按钮
"""
import logging
import asyncio
import random
from typing import Optional, List, Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from telegram.constants import ParseMode

from config import config
from database import db
from extractor import extractor
from reports import report_generator
from search import search_engine

logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram Bot 类"""
    
    def __init__(self):
        self.app: Optional[Application] = None
        self.is_running = False
    
    def create_app(self) -> Application:
        """创建 Application 实例"""
        self.app = Application.builder().token(config.BOT_TOKEN).build()
        
        # 注册命令处理器
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("stats", self.cmd_stats))
        self.app.add_handler(CommandHandler("channels", self.cmd_channels))
        self.app.add_handler(CommandHandler("report", self.cmd_report))
        self.app.add_handler(CommandHandler("search", self.cmd_search))
        self.app.add_handler(CommandHandler("crawler_status", self.cmd_crawler_status))
        self.app.add_handler(CommandHandler("crawler_on", self.cmd_crawler_on))
        self.app.add_handler(CommandHandler("crawler_off", self.cmd_crawler_off))
        self.app.add_handler(CommandHandler("add_channel", self.cmd_add_channel))
        self.app.add_handler(CommandHandler("list", self.cmd_list_channels))
        
        # 注册消息处理器（监听私有频道）
        self.app.add_handler(MessageHandler(
            filters.Chat(chat_id=config.COLLECT_CHANNEL_ID),
            self.handle_channel_message
        ))
        
        # 注册消息处理器（监听搜索群组）
        self.app.add_handler(MessageHandler(
            filters.Chat(chat_id=config.SEARCH_GROUP_ID) & filters.TEXT & ~filters.COMMAND,
            self.handle_search_group_message
        ))
        
        # 注册回调查询处理器（按钮点击）
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # 错误处理器
        self.app.add_error_handler(self.error_handler)
        
        return self.app
    
    async def start(self):
        """启动 Bot"""
        logger.info("🤖 正在启动 Bot...")
        
        if not self.app:
            self.create_app()
        
        self.is_running = True
        
        # 初始化数据库
        await db.init_database()
        
        # 启动轮询
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)
        
        logger.info("✅ Bot 已启动并运行")
    
    async def stop(self):
        """停止 Bot"""
        self.is_running = False
        
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
        
        logger.info("⏹️ Bot 已停止")
    
    # ============ 命令处理器 ============
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        user_id = update.effective_user.id
        is_admin = config.is_admin(user_id)
        
        welcome = "👋 欢迎使用 Telegram 中文搜索 Bot！\n\n"
        welcome += "🔍 功能介绍：\n"
        welcome += "• 自动收集频道链接\n"
        welcome += "• 智能分类管理\n"
        welcome += "• 强大的搜索功能\n"
        welcome += "• 详细的统计报表\n\n"
        
        welcome += "📖 使用方法：\n"
        welcome += "/search <关键词> - 搜索内容\n"
        welcome += "/stats - 查看统计\n"
        welcome += "/help - 查看帮助\n\n"
        
        if is_admin:
            welcome += "👑 管理员功能：\n"
            welcome += "/channels - 频道列表\n"
            welcome += "/report - 详细报表\n"
            welcome += "/crawler_status - 爬虫状态\n"
            welcome += "/add_channel <链接> - 添加频道\n\n"
        
        # 创建主菜单按钮
        keyboard = [
            [
                InlineKeyboardButton("🔍 搜索", callback_data='menu_search'),
                InlineKeyboardButton("📊 统计", callback_data='menu_stats')
            ],
            [
                InlineKeyboardButton("📺 频道列表", callback_data='menu_list'),
                InlineKeyboardButton("❓ 帮助", callback_data='menu_help')
            ],
        ]
        
        if is_admin:
            keyboard.append([
                InlineKeyboardButton("📈 报表", callback_data='menu_report'),
                InlineKeyboardButton("⚙️ 设置", callback_data='menu_settings')
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome, reply_markup=reply_markup)
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /help 命令"""
        help_text = "📖 使用帮助\n"
        help_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        help_text += "📺 频道管理：\n"
        help_text += "/list - 查看已收集的频道列表\n"
        help_text += "  • 支持分类筛选\n"
        help_text += "  • 支持翻页浏览\n"
        help_text += "  • 显示频道链接\n\n"
        
        help_text += "🔍 搜索功能：\n"
        help_text += "/search Python - 基础搜索\n"
        help_text += "/search Python type:video - 只搜视频\n"
        help_text += "/search Python channel:@tech - 指定频道\n\n"
        
        help_text += "📊 统计查询：\n"
        help_text += "/stats - 查看总体统计\n\n"
        
        if config.is_admin(update.effective_user.id):
            help_text += "👑 管理员命令：\n"
            help_text += "/channels - 管理员频道列表\n"
            help_text += "/report - 详细报表\n"
            help_text += "/add_channel <链接> - 手动添加频道\n"
            help_text += "/crawler_status - 查看爬虫状态\n"
            help_text += "/crawler_on - 启用爬虫\n"
            help_text += "/crawler_off - 禁用爬虫\n\n"
        
        help_text += "💡 提示：\n"
        help_text += "• 将频道链接转发到收集频道，Bot 会自动提取\n"
        help_text += "• 搜索支持多关键词（空格分隔）\n"
        help_text += "• 使用按钮界面更方便操作\n"
        
        await update.message.reply_text(help_text)
    
    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /stats 命令"""
        report = await report_generator.generate_overview_report()
        await update.message.reply_text(report)
    
    async def cmd_channels(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /channels 命令"""
        if not config.is_admin(update.effective_user.id):
            await update.message.reply_text("⛔ 此命令仅管理员可用")
            return
        
        # 显示频道列表（第一页）
        await self._show_channels_page(update.message, page=0)
    
    async def cmd_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /report 命令"""
        if not config.is_admin(update.effective_user.id):
            await update.message.reply_text("⛔ 此命令仅管理员可用")
            return
        
        # 显示报表菜单
        keyboard = [
            [InlineKeyboardButton("📊 总体统计", callback_data='report_overview')],
            [InlineKeyboardButton("📺 频道列表", callback_data='report_channels')],
            [InlineKeyboardButton("📁 分类统计", callback_data='report_categories')],
            [InlineKeyboardButton("🔥 热门频道", callback_data='report_top')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📈 请选择报表类型：",
            reply_markup=reply_markup
        )
    
    async def cmd_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /search 命令"""
        if not context.args:
            await update.message.reply_text(
                "🔍 请输入搜索关键词\n\n"
                "用法: /search <关键词>\n"
                "示例: /search Python教程"
            )
            return
        
        query = ' '.join(context.args)
        
        # 执行搜索
        results, total_pages = await search_engine.search(query, page=0)
        
        if not results:
            await update.message.reply_text(f"😔 未找到包含 \"{query}\" 的内容")
            return
        
        # 格式化结果
        response = f"🔍 搜索: \"{query}\"\n"
        response += f"━━━━━━━━━━━━━━━━━━━━\n"
        response += f"找到 {len(results)} 条结果\n\n"
        
        for i, result in enumerate(results[:5], 1):  # 只显示前5条
            response += f"{i}. {result['content'][:80]}...\n"
            if result.get('channel_username'):
                response += f"   📺 @{result['channel_username']}\n"
            response += "\n"
        
        # 添加翻页按钮
        keyboard = []
        if total_pages > 1:
            keyboard.append([
                InlineKeyboardButton(
                    "下一页 ▶️",
                    callback_data=f'search_{query}_1'
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        
        await update.message.reply_text(response, reply_markup=reply_markup)
    
    async def cmd_crawler_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /crawler_status 命令"""
        if not config.is_admin(update.effective_user.id):
            await update.message.reply_text("⛔ 此命令仅管理员可用")
            return
        
        crawler_enabled = await db.get_crawler_status()
        
        status = "⚙️ 爬虫状态\n"
        status += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        if crawler_enabled:
            status += "🟢 状态: 已启用\n"
        else:
            status += "🔴 状态: 已禁用\n"
        
        status += f"\n配置信息:\n"
        status += f"• API ID: {'已配置' if config.API_ID else '未配置'}\n"
        status += f"• API Hash: {'已配置' if config.API_HASH else '未配置'}\n"
        status += f"• 每日限制: {config.MAX_CHANNELS_PER_DAY} 个频道\n"
        
        # 添加控制按钮
        keyboard = [
            [
                InlineKeyboardButton(
                    "🟢 启用爬虫" if not crawler_enabled else "🔴 禁用爬虫",
                    callback_data='crawler_toggle'
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(status, reply_markup=reply_markup)
    
    async def cmd_crawler_on(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /crawler_on 命令"""
        if not config.is_admin(update.effective_user.id):
            await update.message.reply_text("⛔ 此命令仅管理员可用")
            return
        
        # 检查配置
        if not config.API_ID or not config.API_HASH:
            await update.message.reply_text(
                "❌ 无法启用爬虫\n\n"
                "请先在 .env 文件中配置:\n"
                "• API_ID\n"
                "• API_HASH\n"
                "• PHONE_NUMBER\n\n"
                "然后重启 Bot"
            )
            return
        
        await db.set_crawler_status(True)
        await update.message.reply_text(
            "✅ 爬虫已启用\n\n"
            "⚠️ 注意: 需要重启 Bot 才能生效"
        )
    
    async def cmd_crawler_off(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /crawler_off 命令"""
        if not config.is_admin(update.effective_user.id):
            await update.message.reply_text("⛔ 此命令仅管理员可用")
            return
        
        await db.set_crawler_status(False)
        await update.message.reply_text("🔴 爬虫已禁用")
    
    async def cmd_add_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /add_channel 命令"""
        if not config.is_admin(update.effective_user.id):
            await update.message.reply_text("⛔ 此命令仅管理员可用")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📺 请提供频道链接\n\n"
                "用法: /add_channel <链接>\n"
                "示例: /add_channel @tech_news\n"
                "示例: /add_channel https://t.me/tech_news"
            )
            return
        
        channel_link = context.args[0]
        
        # 提取频道信息
        channels = extractor.extract_from_text(channel_link)
        
        if not channels:
            await update.message.reply_text("❌ 无效的频道链接")
            return
        
        channel = channels[0]
        
        # 添加到数据库
        channel_id = await db.add_channel(
            username=channel.username,
            discovered_from=f"manual_{update.effective_user.id}",
            category='未分类'
        )
        
        if channel_id:
            await update.message.reply_text(
                f"✅ 已添加频道: @{channel.username}\n"
                f"ID: {channel_id}"
            )
        else:
            await update.message.reply_text(
                f"ℹ️ 频道已存在: @{channel.username}"
            )
    
    async def cmd_list_channels(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /list 命令 - 显示已收集的频道列表"""
        # 显示频道列表首页（带分类按钮）
        await self._show_channels_list_page(update.message, page=0, category=None)
    
    # ============ 消息处理器 ============
    
    async def handle_channel_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理私有频道的消息（提取链接）"""
        # 频道消息使用 effective_message（兼容 channel_post 和 message）
        message = update.effective_message
        
        if not message:
            return
        
        # 收集所有链接（从文本和实体中）
        all_links = []
        
        # 1. 从纯文本中提取链接
        if message.text:
            text_channels = extractor.extract_from_text(message.text)
            all_links.extend([ch.url for ch in text_channels])
            logger.info(f"📝 从文本提取到 {len(text_channels)} 个链接")
        
        # 2. 从 MessageEntity 中提取链接
        if message.entities:
            for entity in message.entities:
                # TEXT_LINK: 链接隐藏在文字中
                if entity.type == 'text_link' and entity.url:
                    all_links.append(entity.url)
                # URL: 纯文本URL（已经在上面提取过了，这里可以跳过）
                elif entity.type == 'url' and message.text:
                    url_text = message.text[entity.offset:entity.offset + entity.length]
                    all_links.append(url_text)
            
            entity_count = len([e for e in message.entities if e.type in ['text_link', 'url']])
            if entity_count > 0:
                logger.info(f"🔗 从实体提取到 {entity_count} 个链接")
        
        if not all_links:
            logger.debug(f"⚠️ 消息 {message.message_id} 中没有找到任何链接")
            return
        
        logger.info(f"📊 总共收集到 {len(all_links)} 个链接")
        
        # 3. 处理所有链接（添加速率限制和验证）
        added_count = 0
        skipped_count = 0
        
        for link in all_links:
            # 使用 extractor 提取标准化的频道信息
            channels = extractor.extract_from_text(link)
            
            for channel in channels:
                # 跳过 Bot（username 以 'bot' 结尾的）
                if channel.username.lower().endswith('bot'):
                    logger.info(f"⏭️ 跳过 Bot: @{channel.username}")
                    skipped_count += 1
                    continue
                
                # 检查数据库中是否已存在
                existing = await db.get_channel_by_username(channel.username)
                if existing:
                    logger.info(f"⏭️ 频道已存在: @{channel.username}")
                    skipped_count += 1
                    continue
                
                # 智能分类
                category = extractor.categorize_channel(message.text or "")
                
                # 尝试获取频道的详细信息（名称、成员数等）
                channel_title = None
                channel_id_str = None
                member_count = None
                is_verified = False
                channel_exists = False
                
                try:
                    # 添加延迟，避免触发速率限制
                    # 基础延迟 + 随机延迟，让请求更自然
                    base_delay = config.CHANNEL_VERIFY_DELAY
                    random_delay = random.uniform(0, config.CHANNEL_VERIFY_RANDOM_DELAY)
                    total_delay = base_delay + random_delay
                    
                    logger.debug(f"⏱️ 等待 {total_delay:.1f} 秒后验证 @{channel.username}")
                    await asyncio.sleep(total_delay)
                    
                    # 使用 Bot API 获取频道信息（验证是否存在）
                    chat = await context.bot.get_chat(f"@{channel.username}")
                    
                    # 检查是否为频道或群组
                    if chat.type not in ['channel', 'supergroup', 'group']:
                        logger.warning(f"⏭️ 跳过非频道/群组: @{channel.username} (类型: {chat.type})")
                        skipped_count += 1
                        continue
                    
                    channel_title = chat.title
                    channel_id_str = str(chat.id)
                    channel_exists = True
                    
                    # 尝试获取成员数（可能需要权限）
                    try:
                        member_count = await context.bot.get_chat_member_count(chat.id)
                    except:
                        pass
                    
                    logger.info(f"📋 获取频道信息: {channel_title} (@{channel.username})")
                    
                except Exception as e:
                    error_msg = str(e)
                    
                    # 如果是频道不存在，跳过
                    if "not found" in error_msg.lower() or "chat not found" in error_msg.lower():
                        logger.warning(f"❌ 频道不存在，跳过: @{channel.username}")
                        skipped_count += 1
                        continue
                    
                    # 如果是速率限制，记录警告但继续（保存基本信息）
                    elif "flood" in error_msg.lower() or "too many requests" in error_msg.lower():
                        logger.warning(f"⏳ 速率限制: @{channel.username} - {error_msg}")
                        # 继续保存，但没有详细信息
                    
                    # 其他错误
                    else:
                        logger.warning(f"⚠️ 无法获取 @{channel.username} 的详细信息: {e}")
                
                # 只有在频道存在或无法验证时才添加到数据库
                # 如果明确知道频道不存在，则已经在上面 continue 跳过了
                if channel_exists or channel_title:
                    # 添加到数据库
                    db_id = await db.add_channel(
                        username=channel.username,
                        channel_id=channel_id_str,
                        title=channel_title,
                        discovered_from=str(message.message_id),
                        category=category
                    )
                    
                    if db_id:
                        added_count += 1
                        display_name = channel_title if channel_title else f"@{channel.username}"
                        logger.info(f"✅ 新频道: {display_name} - {category}")
                        
                        # 如果获取到了成员数，更新到数据库
                        if member_count:
                            await db.update_channel_by_username(channel.username, member_count=member_count)
                        
                        # 发送频道元信息到 SearchDataStore 频道（利用 Telegram 无限存储）
                        try:
                            await self._save_channel_metadata_to_storage(
                                channel_username=channel.username,
                                channel_title=channel_title,
                                channel_id=channel_id_str,
                                member_count=member_count,
                                category=category,
                                discovered_from=str(message.message_id),
                                context=context
                            )
                        except Exception as e:
                            logger.warning(f"⚠️ 无法发送频道元信息到存储频道: {e}")
        
        # 输出统计信息
        if added_count > 0 or skipped_count > 0:
            summary = f"📺 消息 {message.message_id} 处理完成："
            if added_count > 0:
                summary += f" ✅ 新增 {added_count} 个"
            if skipped_count > 0:
                summary += f" ⏭️ 跳过 {skipped_count} 个"
            logger.info(summary)
        else:
            logger.info(f"ℹ️ 消息 {message.message_id} 中没有有效的频道链接")
    
    async def handle_search_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理搜索群组的消息（执行搜索）"""
        message = update.effective_message
        
        if not message or not message.text:
            return
        
        query = message.text.strip()
        
        if not query or len(query) < 2:
            return  # 忽略过短的查询
        
        logger.info(f"🔍 群组搜索: {query} (用户: {update.effective_user.id})")
        
        # 执行搜索
        try:
            results, total_pages = await search_engine.search(query, page=0)
            
            # 格式化并发送结果
            await self._send_search_results(
                message=message,
                query=query,
                results=results,
                page=0,
                total_pages=total_pages,
                media_filter=None
            )
        except Exception as e:
            logger.error(f"搜索出错: {e}")
            await message.reply_text("❌ 搜索出错，请稍后重试")
    
    # ============ 回调处理器 ============
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理按钮回调"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        # 菜单回调
        if data == 'menu_search':
            await query.message.reply_text(
                "🔍 搜索功能\n\n"
                "使用方法: /search <关键词>\n"
                "示例: /search Python教程"
            )
        
        elif data == 'menu_stats':
            report = await report_generator.generate_overview_report()
            await query.message.reply_text(report)
        
        elif data == 'menu_list':
            await self._show_channels_list_page(query.message, page=0, category=None)
        
        elif data == 'menu_channels':
            # 管理员专用功能
            if not config.is_admin(query.from_user.id):
                await query.answer("⛔ 此功能仅管理员可用", show_alert=True)
                return
            await self._show_channels_page(query.message, page=0)
        
        elif data == 'menu_report':
            # 管理员专用功能
            if not config.is_admin(query.from_user.id):
                await query.answer("⛔ 此功能仅管理员可用", show_alert=True)
                return
            keyboard = [
                [InlineKeyboardButton("📊 总体统计", callback_data='report_overview')],
                [InlineKeyboardButton("📺 频道列表", callback_data='report_channels')],
                [InlineKeyboardButton("📁 分类统计", callback_data='report_categories')],
                [InlineKeyboardButton("🔥 热门频道", callback_data='report_top')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text("📈 请选择报表类型：", reply_markup=reply_markup)
        
        elif data == 'menu_settings':
            # 管理员专用功能
            if not config.is_admin(query.from_user.id):
                await query.answer("⛔ 此功能仅管理员可用", show_alert=True)
                return
            await query.message.reply_text(
                "⚙️ 设置\n\n"
                "使用命令管理爬虫:\n"
                "/crawler_status - 查看状态\n"
                "/crawler_on - 启用爬虫\n"
                "/crawler_off - 禁用爬虫"
            )
        
        elif data == 'menu_help':
            await self.cmd_help(update, context)
        
        # 报表回调（管理员专用）
        elif data == 'report_overview':
            if not config.is_admin(query.from_user.id):
                await query.answer("⛔ 此功能仅管理员可用", show_alert=True)
                return
            report = await report_generator.generate_overview_report()
            await query.message.reply_text(report)
        
        elif data == 'report_channels':
            if not config.is_admin(query.from_user.id):
                await query.answer("⛔ 此功能仅管理员可用", show_alert=True)
                return
            await self._show_channels_page(query.message, page=0)
        
        elif data == 'report_categories':
            if not config.is_admin(query.from_user.id):
                await query.answer("⛔ 此功能仅管理员可用", show_alert=True)
                return
            report = await report_generator.generate_category_report()
            await query.message.reply_text(report)
        
        elif data == 'report_top':
            if not config.is_admin(query.from_user.id):
                await query.answer("⛔ 此功能仅管理员可用", show_alert=True)
                return
            report = await report_generator.generate_top_channels_report(limit=10)
            await query.message.reply_text(report)
        
        # 频道列表翻页（管理员专用）
        elif data.startswith('channels_page_'):
            if not config.is_admin(query.from_user.id):
                await query.answer("⛔ 此功能仅管理员可用", show_alert=True)
                return
            page = int(data.split('_')[-1])
            await self._show_channels_page(query.message, page=page, edit=True)
        
        # 爬虫开关（管理员专用）
        elif data == 'crawler_toggle':
            if not config.is_admin(query.from_user.id):
                await query.answer("⛔ 此功能仅管理员可用", show_alert=True)
                return
            current_status = await db.get_crawler_status()
            new_status = not current_status
            await db.set_crawler_status(new_status)
            
            status_text = "启用" if new_status else "禁用"
            await query.message.reply_text(
                f"✅ 爬虫已{status_text}\n\n"
                "⚠️ 注意: 需要重启 Bot 才能生效"
            )
        
        # 搜索类型过滤
        elif data.startswith('search_type_'):
            parts = data.split('_')
            if len(parts) >= 4:
                query_text = parts[2]
                media_type = parts[3]
                page = int(parts[4]) if len(parts) > 4 else 0
                
                # 执行搜索（带类型过滤）
                media_filter = None if media_type == 'all' else media_type
                results, total_pages = await search_engine.search(
                    query_text,
                    page=page,
                    media_type_filter=media_filter
                )
                
                # 更新显示
                await self._send_search_results(
                    message=query.message,
                    query=query_text,
                    results=results,
                    page=page,
                    total_pages=total_pages,
                    media_filter=media_filter,
                    edit=True
                )
        
        # 搜索翻页
        elif data.startswith('search_page_'):
            parts = data.split('_')
            if len(parts) >= 4:
                query_text = parts[2]
                media_type = parts[3]
                page = int(parts[4]) if len(parts) > 4 else 0
                
                # 执行搜索
                media_filter = None if media_type == 'all' else media_type
                results, total_pages = await search_engine.search(
                    query_text,
                    page=page,
                    media_type_filter=media_filter
                )
                
                # 更新显示
                await self._send_search_results(
                    message=query.message,
                    query=query_text,
                    results=results,
                    page=page,
                    total_pages=total_pages,
                    media_filter=media_filter,
                    edit=True
                )
        
        # 频道列表 - 分类筛选
        elif data.startswith('list_cat_'):
            parts = data.split('_')
            if len(parts) >= 3:
                category = parts[2]
                page = int(parts[3]) if len(parts) > 3 else 0
                
                # 显示筛选后的列表
                category_filter = None if category == 'all' else category
                await self._show_channels_list_page(
                    message=query.message,
                    page=page,
                    category=category_filter,
                    edit=True
                )
        
        # 频道列表 - 翻页
        elif data.startswith('list_page_'):
            parts = data.split('_')
            if len(parts) >= 3:
                category = parts[2]
                page = int(parts[3]) if len(parts) > 3 else 0
                
                # 显示指定页
                category_filter = None if category == 'all' else category
                await self._show_channels_list_page(
                    message=query.message,
                    page=page,
                    category=category_filter,
                    edit=True
                )
    
    # ============ 辅助方法 ============
    
    async def _save_channel_metadata_to_storage(
        self,
        channel_username: str,
        channel_title: str,
        channel_id: str,
        member_count: int,
        category: str,
        discovered_from: str = None,
        context: ContextTypes.DEFAULT_TYPE = None
    ):
        """
        将频道元信息保存到存储频道
        利用 Telegram 的无限存储，备份频道元数据
        这样频道信息本身也成为可搜索的数据
        """
        if not config.STORAGE_CHANNEL_ID:
            return
        
        # 格式化频道元信息卡片
        from datetime import datetime
        
        card = "📺 新频道收录\n"
        card += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # 基本信息
        if channel_title:
            card += f"📝 名称: {channel_title}\n"
        card += f"🔗 用户名: @{channel_username}\n"
        
        if channel_id:
            card += f"🆔 频道ID: {channel_id}\n"
        
        card += f"📁 分类: {category}\n"
        
        if member_count:
            # 格式化成员数（带简写和完整数字）
            if member_count >= 1000000:
                member_str = f"{member_count/1000000:.1f}M"
            elif member_count >= 1000:
                member_str = f"{member_count/1000:.1f}K"
            else:
                member_str = str(member_count)
            card += f"👥 成员: {member_str} ({member_count:,})\n"
        
        # 时间戳和来源
        now = datetime.now()
        card += f"🕐 收录时间: {now.strftime('%Y-%m-%d %H:%M')}\n"
        if discovered_from:
            card += f"📊 来源: 消息 #{discovered_from}\n"
        
        card += f"\n🔗 https://t.me/{channel_username}\n\n"
        
        # 标签（用于搜索和分类）
        tags = ["#频道元信息", f"#{category.replace(' ', '_')}"]
        if member_count:
            if member_count >= 100000:
                tags.append("#超10万")
            elif member_count >= 10000:
                tags.append("#超1万")
            elif member_count >= 1000:
                tags.append("#超1千")
        
        card += " ".join(tags)
        card += "\n━━━━━━━━━━━━━━━━━━━━"
        
        try:
            # 发送到存储频道
            await context.bot.send_message(
                chat_id=config.STORAGE_CHANNEL_ID,
                text=card,
                disable_web_page_preview=False  # 显示频道预览
            )
            logger.info(f"💾 已保存频道元信息到存储频道: @{channel_username}")
        except Exception as e:
            logger.error(f"❌ 保存频道元信息失败: {e}")
            raise
    
    async def _send_search_results(
        self,
        message,
        query: str,
        results: List[Dict],
        page: int = 0,
        total_pages: int = 1,
        media_filter: str = None,
        edit: bool = False
    ):
        """发送格式化的搜索结果（带广告、分类按钮、翻页）"""
        
        # 构建响应文本
        response = ""
        
        # 1. 顶部广告位
        if config.SEARCH_AD_ENABLED and config.SEARCH_AD_TEXT:
            response += f"📢 {config.SEARCH_AD_TEXT}\n"
            response += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # 2. 搜索结果
        if not results:
            response += f"🔍 搜索: \"{query}\"\n\n"
            response += "😔 未找到相关内容\n\n"
            response += "💡 提示:\n"
            response += "• 尝试其他关键词\n"
            response += "• 检查拼写是否正确\n"
            response += "• 使用更通用的词语"
        else:
            response += f"🔍 搜索: \"{query}\"\n"
            if media_filter:
                response += f"📁 类型: {self._get_media_type_name(media_filter)}\n"
            response += f"━━━━━━━━━━━━━━━━━━━━\n"
            response += f"📊 找到 {len(results)} 条结果\n\n"
            
            # 格式化每条结果
            for i, result in enumerate(results, 1):
                result_text = search_engine.format_search_result(
                    result,
                    keywords=[query],
                    index=i
                )
                response += result_text + "\n\n"
        
        # 3. 类型分类按钮
        keyboard = []
        
        # 第一行：媒体类型按钮
        type_buttons = [
            InlineKeyboardButton("📝 全部", callback_data=f'search_type_{query}_all_{page}'),
            InlineKeyboardButton("🎬 视频", callback_data=f'search_type_{query}_video_{page}'),
            InlineKeyboardButton("📸 图片", callback_data=f'search_type_{query}_photo_{page}'),
            InlineKeyboardButton("📎 文档", callback_data=f'search_type_{query}_document_{page}'),
        ]
        keyboard.append(type_buttons)
        
        # 第二行：翻页按钮
        if total_pages > 1 or page > 0:
            nav_buttons = []
            
            if page > 0:
                nav_buttons.append(
                    InlineKeyboardButton("◀️ 上一页", callback_data=f'search_page_{query}_{media_filter or "all"}_{page-1}')
                )
            
            nav_buttons.append(
                InlineKeyboardButton(f"{page+1}/{max(total_pages, 1)}", callback_data='noop')
            )
            
            if results and len(results) >= config.RESULTS_PER_PAGE:
                nav_buttons.append(
                    InlineKeyboardButton("下一页 ▶️", callback_data=f'search_page_{query}_{media_filter or "all"}_{page+1}')
                )
            
            if nav_buttons:
                keyboard.append(nav_buttons)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # 发送消息
        try:
            if edit and hasattr(message, 'edit_text'):
                await message.edit_text(
                    response,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
            else:
                await message.reply_text(
                    response,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
        except Exception as e:
            logger.error(f"发送搜索结果失败: {e}")
            # 如果Markdown解析失败，尝试不带格式发送
            await message.reply_text(response, reply_markup=reply_markup)
    
    def _get_media_type_name(self, media_type: str) -> str:
        """获取媒体类型的中文名称"""
        type_names = {
            'video': '🎬 视频',
            'photo': '📸 图片',
            'document': '📎 文档',
            'audio': '🎵 音频',
            'text': '📝 文本'
        }
        return type_names.get(media_type, media_type)
    
    async def _show_channels_page(self, message, page: int = 0, edit: bool = False):
        """显示频道列表（分页）"""
        per_page = 10
        report, total_pages = await report_generator.generate_channels_list(
            page=page,
            per_page=per_page
        )
        
        # 创建翻页按钮
        keyboard = []
        nav_buttons = []
        
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton("◀️ 上一页", callback_data=f'channels_page_{page-1}')
            )
        
        nav_buttons.append(
            InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data='noop')
        )
        
        if page < total_pages - 1:
            nav_buttons.append(
                InlineKeyboardButton("下一页 ▶️", callback_data=f'channels_page_{page+1}')
            )
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        
        if edit:
            await message.edit_text(report, reply_markup=reply_markup)
        else:
            await message.reply_text(report, reply_markup=reply_markup)
    
    async def _show_channels_list_page(self, message, page: int = 0, category: str = None, edit: bool = False):
        """显示用户友好的频道列表（带分类筛选）"""
        per_page = 15
        
        # 获取统计信息
        total_channels = await db.get_channels_count()
        category_stats = await db.get_channels_by_category()
        
        # 获取频道列表
        channels = await db.get_all_channels(
            category=category,
            limit=per_page,
            offset=page * per_page
        )
        
        # 计算总页数
        if category:
            filtered_count = category_stats.get(category, 0)
        else:
            filtered_count = total_channels
        total_pages = max(1, (filtered_count + per_page - 1) // per_page)
        
        # 构建消息
        response = "📺 已收集的频道列表\n"
        response += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        response += f"📊 总计: {total_channels} 个频道\n"
        if category:
            response += f"📁 当前分类: {category} ({filtered_count} 个)\n"
        response += f"📄 第 {page + 1}/{total_pages} 页\n\n"
        
        if not channels:
            response += "😔 暂无频道数据\n\n"
            response += "💡 转发包含频道链接的消息到收集频道即可自动提取"
        else:
            # 表格形式显示
            response += "```\n"
            response += f"{'序号':<4} {'频道名称':<20} {'用户名':<15}\n"
            response += f"{'-'*4} {'-'*20} {'-'*15}\n"
            
            for i, ch in enumerate(channels, 1):
                num = page * per_page + i
                username = ch['channel_username']
                title = ch.get('channel_title') or '未知'
                
                # 截断过长的名称
                if len(title) > 18:
                    title = title[:15] + '...'
                if len(username) > 13:
                    username = username[:10] + '...'
                
                response += f"{num:<4} {title:<20} @{username:<14}\n"
            
            response += "```\n\n"
            
            # 添加分类说明
            if category:
                response += f"📁 分类: {category}\n"
            
            # 添加链接提示
            response += "💡 点击用户名可直接访问频道"
        
        # 创建按钮
        keyboard = []
        
        # 第一行：分类筛选按钮
        category_buttons = []
        category_buttons.append(
            InlineKeyboardButton(
                "📝 全部" if not category else "全部",
                callback_data='list_cat_all_0'
            )
        )
        
        # 显示前3个最多的分类
        sorted_cats = sorted(category_stats.items(), key=lambda x: x[1], reverse=True)[:3]
        for cat_name, count in sorted_cats:
            emoji = self._get_category_emoji(cat_name)
            button_text = f"{emoji} {cat_name}" if category != cat_name else cat_name
            category_buttons.append(
                InlineKeyboardButton(
                    button_text,
                    callback_data=f'list_cat_{cat_name}_0'
                )
            )
        
        if category_buttons:
            # 分成两行显示
            keyboard.append(category_buttons[:2])
            if len(category_buttons) > 2:
                keyboard.append(category_buttons[2:])
        
        # 第二行：翻页按钮
        if total_pages > 1:
            nav_buttons = []
            if page > 0:
                nav_buttons.append(
                    InlineKeyboardButton(
                        "◀️ 上一页",
                        callback_data=f'list_page_{category or "all"}_{page-1}'
                    )
                )
            
            nav_buttons.append(
                InlineKeyboardButton(
                    f"{page+1}/{total_pages}",
                    callback_data='noop'
                )
            )
            
            if page < total_pages - 1:
                nav_buttons.append(
                    InlineKeyboardButton(
                        "下一页 ▶️",
                        callback_data=f'list_page_{category or "all"}_{page+1}'
                    )
                )
            
            if nav_buttons:
                keyboard.append(nav_buttons)
        
        # 第三行：刷新按钮
        keyboard.append([
            InlineKeyboardButton("🔄 刷新", callback_data=f'list_page_{category or "all"}_{page}')
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # 发送或编辑消息
        try:
            if edit and hasattr(message, 'edit_text'):
                await message.edit_text(response, reply_markup=reply_markup, disable_web_page_preview=True)
            else:
                await message.reply_text(response, reply_markup=reply_markup, disable_web_page_preview=True)
        except Exception as e:
            logger.error(f"显示频道列表失败: {e}")
            await message.reply_text(response, reply_markup=reply_markup)
    
    def _get_category_emoji(self, category: str) -> str:
        """获取分类 emoji"""
        emoji_map = {
            '新闻资讯': '📰',
            '科技数码': '📱',
            '影视资源': '🎬',
            '软件工具': '🔧',
            '电子书籍': '📚',
            '学习教育': '🎓',
            '资源分享': '📦',
            '娱乐休闲': '🎮',
            '生活服务': '🏪',
            '金融投资': '💰',
            '其他': '📁',
        }
        return emoji_map.get(category, '📁')
    
    # ============ 错误处理 ============
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """错误处理器"""
        logger.error(f"处理更新时出错: {context.error}", exc_info=context.error)
        
        # 记录更新的基本信息（避免记录完整的 update 对象）
        if update:
            update_info = {
                'update_id': update.update_id,
                'message_id': update.effective_message.message_id if update.effective_message else None,
                'chat_id': update.effective_chat.id if update.effective_chat else None,
                'user_id': update.effective_user.id if update.effective_user else None,
            }
            logger.error(f"更新信息: {update_info}")


# 创建全局 Bot 实例
bot = TelegramBot()

