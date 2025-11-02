"""
报表生成模块
生成各类统计报表和数据可视化
"""
from typing import Dict, List
from datetime import datetime
from database import db


class ReportGenerator:
    """报表生成器类"""
    
    async def generate_overview_report(self) -> str:
        """生成总体统计报表"""
        # 获取统计数据
        total_channels = await db.get_channels_count()
        verified_channels = await db.get_channels_count(status='active')
        pending_channels = await db.get_channels_count(status='pending')
        failed_channels = await db.get_channels_count(status='failed')
        
        total_messages = await db.get_messages_count()
        
        media_stats = await db.get_messages_by_media_type()
        
        crawler_status = await db.get_crawler_status()
        
        # 生成报表文本
        report = "📊 系统总体统计\n"
        report += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        report += f"📺 频道统计：\n"
        report += f"  • 总计: {total_channels} 个\n"
        report += f"  • 已验证: {verified_channels} 个 ✅\n"
        report += f"  • 待验证: {pending_channels} 个 ⏳\n"
        report += f"  • 失效/封禁: {failed_channels} 个 ❌\n\n"
        
        report += f"📄 消息统计：\n"
        report += f"  • 总计: {total_messages:,} 条\n"
        for media_type, count in media_stats.items():
            emoji = self._get_media_emoji(media_type)
            report += f"  • {emoji} {media_type}: {count:,}\n"
        report += "\n"
        
        report += f"⚙️ 爬虫状态：\n"
        status_emoji = "🟢" if crawler_status else "🔴"
        status_text = "已启用" if crawler_status else "已禁用"
        report += f"  • {status_emoji} {status_text}\n\n"
        
        report += f"🕐 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return report
    
    async def generate_channels_list(
        self, 
        page: int = 0, 
        per_page: int = 10,
        category: str = None
    ) -> tuple[str, int]:
        """生成频道列表报表（分页）"""
        offset = page * per_page
        channels = await db.get_all_channels(
            category=category,
            limit=per_page,
            offset=offset
        )
        
        total_count = await db.get_channels_count()
        total_pages = (total_count + per_page - 1) // per_page
        
        if not channels:
            return "📭 暂无频道数据", total_pages
        
        report = f"📺 频道列表 (第 {page + 1}/{total_pages} 页)\n"
        if category:
            report += f"📁 分类: {category}\n"
        report += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, channel in enumerate(channels, 1):
            status_emoji = self._get_status_emoji(channel['status'])
            verified_emoji = "✅" if channel['is_verified'] else ""
            
            report += f"{offset + i}. {status_emoji} {verified_emoji}\n"
            report += f"   @{channel['channel_username']}\n"
            
            if channel['channel_title']:
                report += f"   📝 {channel['channel_title']}\n"
            
            report += f"   📁 {channel['category']}\n"
            
            if channel['member_count']:
                report += f"   👥 {channel['member_count']:,} 成员\n"
            
            discovered = datetime.fromisoformat(channel['discovered_date'])
            report += f"   🕐 {discovered.strftime('%Y-%m-%d')}\n"
            
            report += "\n"
        
        return report, total_pages
    
    async def generate_category_report(self) -> str:
        """生成分类统计报表"""
        category_stats = await db.get_channels_by_category()
        
        if not category_stats:
            return "📊 暂无分类数据"
        
        total = sum(category_stats.values())
        
        report = "📊 频道分类统计\n"
        report += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # 按数量排序
        sorted_categories = sorted(
            category_stats.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for category, count in sorted_categories:
            percentage = (count / total * 100) if total > 0 else 0
            bar = self._create_progress_bar(percentage)
            emoji = self._get_category_emoji(category)
            
            report += f"{emoji} {category}\n"
            report += f"{bar} {count} 个 ({percentage:.1f}%)\n\n"
        
        return report
    
    async def generate_top_channels_report(self, limit: int = 10) -> str:
        """生成热门频道报表（按消息数量）"""
        # 获取每个频道的消息数量
        async with db.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT 
                    c.channel_username,
                    c.channel_title,
                    c.category,
                    COUNT(m.id) as message_count
                FROM channels c
                LEFT JOIN messages m ON c.id = m.channel_id
                WHERE c.status = 'active'
                GROUP BY c.id
                HAVING message_count > 0
                ORDER BY message_count DESC
                LIMIT ?
            """, (limit,))
            rows = await cursor.fetchall()
            channels = [dict(row) for row in rows]
        
        if not channels:
            return "🔥 暂无活跃频道数据"
        
        report = f"🔥 最活跃频道 Top {limit}\n"
        report += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, channel in enumerate(channels, 1):
            medal = self._get_rank_medal(i)
            report += f"{medal} {i}. @{channel['channel_username']}\n"
            
            if channel['channel_title']:
                report += f"   📝 {channel['channel_title']}\n"
            
            report += f"   📁 {channel['category']}\n"
            report += f"   📄 {channel['message_count']:,} 条消息\n\n"
        
        return report
    
    async def generate_search_result_report(
        self,
        results: List[Dict],
        keyword: str,
        page: int = 0,
        total_pages: int = 1
    ) -> str:
        """生成搜索结果报表"""
        if not results:
            return f"🔍 未找到包含 \"{keyword}\" 的内容"
        
        report = f"🔍 搜索结果: \"{keyword}\"\n"
        report += f"━━━━━━━━━━━━━━━━━━━━\n"
        report += f"📄 找到 {len(results)} 条结果 (第 {page + 1}/{total_pages} 页)\n\n"
        
        for i, result in enumerate(results, 1):
            report += f"{i}. "
            
            # 消息内容预览
            content = result['content'][:100]
            if len(result['content']) > 100:
                content += "..."
            report += f"{content}\n"
            
            # 来源频道
            if result.get('channel_username'):
                report += f"   📺 @{result['channel_username']}"
                if result.get('channel_title'):
                    report += f" ({result['channel_title']})"
                report += "\n"
            
            # 媒体类型
            if result['media_type'] != 'text':
                emoji = self._get_media_emoji(result['media_type'])
                report += f"   {emoji} {result['media_type']}\n"
            
            # 时间
            if result.get('publish_date'):
                pub_date = datetime.fromisoformat(result['publish_date'])
                report += f"   🕐 {pub_date.strftime('%Y-%m-%d %H:%M')}\n"
            
            # 链接
            if result.get('storage_message_id'):
                report += f"   🔗 消息ID: {result['storage_message_id']}\n"
            
            report += "\n"
        
        return report
    
    def _get_status_emoji(self, status: str) -> str:
        """获取状态对应的 emoji"""
        emoji_map = {
            'pending': '⏳',
            'active': '✅',
            'failed': '❌',
            'banned': '🚫',
        }
        return emoji_map.get(status, '❓')
    
    def _get_media_emoji(self, media_type: str) -> str:
        """获取媒体类型对应的 emoji"""
        emoji_map = {
            'text': '📝',
            'photo': '📸',
            'video': '🎬',
            'document': '📎',
            'audio': '🎵',
            'voice': '🎤',
            'sticker': '🎨',
            'animation': '🎞️',
        }
        return emoji_map.get(media_type, '📄')
    
    def _get_category_emoji(self, category: str) -> str:
        """获取分类对应的 emoji"""
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
            'uncategorized': '📂',
        }
        return emoji_map.get(category, '📁')
    
    def _get_rank_medal(self, rank: int) -> str:
        """获取排名奖牌"""
        medals = {1: '🥇', 2: '🥈', 3: '🥉'}
        return medals.get(rank, '🏅')
    
    def _create_progress_bar(self, percentage: float, length: int = 10) -> str:
        """创建进度条"""
        filled = int(percentage / 100 * length)
        bar = '█' * filled + '░' * (length - filled)
        return f"[{bar}]"


# 创建全局报表生成器实例
report_generator = ReportGenerator()

