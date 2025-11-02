"""
Bot 主程序
处理用户交互、命令和按钮
"""
import logging
from typing import Optional
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
        ]
        
        if is_admin:
            keyboard.append([
                InlineKeyboardButton("📺 频道", callback_data='menu_channels'),
                InlineKeyboardButton("📈 报表", callback_data='menu_report')
            ])
            keyboard.append([
                InlineKeyboardButton("⚙️ 设置", callback_data='menu_settings'),
                InlineKeyboardButton("❓ 帮助", callback_data='menu_help')
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("❓ 帮助", callback_data='menu_help')
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome, reply_markup=reply_markup)
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /help 命令"""
        help_text = "📖 使用帮助\n"
        help_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        help_text += "🔍 搜索功能：\n"
        help_text += "/search Python - 基础搜索\n"
        help_text += "/search Python type:video - 只搜视频\n"
        help_text += "/search Python channel:@tech - 指定频道\n\n"
        
        help_text += "📊 统计查询：\n"
        help_text += "/stats - 查看总体统计\n\n"
        
        if config.is_admin(update.effective_user.id):
            help_text += "👑 管理员命令：\n"
            help_text += "/channels - 查看频道列表\n"
            help_text += "/report - 详细报表\n"
            help_text += "/add_channel <链接> - 添加频道\n"
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
    
    # ============ 消息处理器 ============
    
    async def handle_channel_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理私有频道的消息（提取链接）"""
        message = update.message
        
        if not message.text:
            return
        
        # 提取频道链接
        channels = extractor.extract_from_text(message.text)
        
        if not channels:
            return
        
        added_count = 0
        for channel in channels:
            # 智能分类
            category = extractor.categorize_channel(message.text)
            
            # 添加到数据库
            channel_id = await db.add_channel(
                username=channel.username,
                discovered_from=str(message.message_id),
                category=category
            )
            
            if channel_id:
                added_count += 1
                logger.info(f"✅ 新频道: @{channel.username} - {category}")
        
        if added_count > 0:
            # 可选：回复消息确认
            # await message.reply_text(f"✅ 已提取 {added_count} 个频道")
            logger.info(f"📺 从消息 {message.message_id} 提取了 {added_count} 个频道")
    
    async def handle_search_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理搜索群组的消息（执行搜索）"""
        message = update.message
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
        
        elif data == 'menu_channels':
            await self._show_channels_page(query.message, page=0)
        
        elif data == 'menu_report':
            keyboard = [
                [InlineKeyboardButton("📊 总体统计", callback_data='report_overview')],
                [InlineKeyboardButton("📺 频道列表", callback_data='report_channels')],
                [InlineKeyboardButton("📁 分类统计", callback_data='report_categories')],
                [InlineKeyboardButton("🔥 热门频道", callback_data='report_top')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text("📈 请选择报表类型：", reply_markup=reply_markup)
        
        elif data == 'menu_settings':
            await query.message.reply_text(
                "⚙️ 设置\n\n"
                "使用命令管理爬虫:\n"
                "/crawler_status - 查看状态\n"
                "/crawler_on - 启用爬虫\n"
                "/crawler_off - 禁用爬虫"
            )
        
        elif data == 'menu_help':
            await self.cmd_help(update, context)
        
        # 报表回调
        elif data == 'report_overview':
            report = await report_generator.generate_overview_report()
            await query.message.reply_text(report)
        
        elif data == 'report_channels':
            await self._show_channels_page(query.message, page=0)
        
        elif data == 'report_categories':
            report = await report_generator.generate_category_report()
            await query.message.reply_text(report)
        
        elif data == 'report_top':
            report = await report_generator.generate_top_channels_report(limit=10)
            await query.message.reply_text(report)
        
        # 频道列表翻页
        elif data.startswith('channels_page_'):
            page = int(data.split('_')[-1])
            await self._show_channels_page(query.message, page=page, edit=True)
        
        # 爬虫开关
        elif data == 'crawler_toggle':
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
    
    # ============ 辅助方法 ============
    
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
    
    # ============ 错误处理 ============
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """错误处理器"""
        logger.error(f"Update {update} caused error {context.error}")


# 创建全局 Bot 实例
bot = TelegramBot()

