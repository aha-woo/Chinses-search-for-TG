"""
搜索引擎模块
提供关键词搜索和结果处理功能
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import re

from database import db
from config import config


class SearchEngine:
    """搜索引擎类"""
    
    def __init__(self):
        self.results_per_page = 10
    
    async def search(
        self,
        query: str,
        page: int = 0,
        channel_filter: str = None,
        media_type_filter: str = None,
        date_filter: str = None
    ) -> Tuple[List[Dict], int, int]:
        """
        执行搜索（联合搜索channels和messages表）
        
        Args:
            query: 搜索关键词
            page: 页码（从0开始）
            channel_filter: 频道过滤（@username）
            media_type_filter: 媒体类型过滤
            date_filter: 日期过滤（YYYY-MM-DD）
        
        Returns:
            (搜索结果列表, 总页数, 总数量)
        """
        # 解析查询字符串
        keywords, filters = self._parse_query(query)
        
        # 合并过滤器
        if channel_filter:
            filters['channel'] = channel_filter
        if media_type_filter:
            filters['media_type'] = media_type_filter
        if date_filter:
            filters['date'] = date_filter
        
        # 如果指定了频道过滤，只搜索该频道
        if filters.get('channel'):
            username = filters['channel'].lstrip('@')
            channel = await db.get_channel_by_username(username)
            if channel:
                channel_id = channel['id']
                # 只搜索该频道的消息
                total_count = await db.search_messages_count(
                    keywords=keywords,
                    channel_id=channel_id,
                    media_type=filters.get('media_type')
                )
                total_pages = max(1, (total_count + self.results_per_page - 1) // self.results_per_page)
                offset = page * self.results_per_page
                results = await db.search_messages(
                    keywords=keywords,
                    channel_id=channel_id,
                    media_type=filters.get('media_type'),
                    limit=self.results_per_page,
                    offset=offset
                )
                return results, total_pages, total_count
        
        # 联合搜索：同时搜索channels和messages表
        # 使用关键词列表（OR逻辑）
        search_keywords = keywords if keywords else [query]
        
        # 获取总数
        counts = await db.search_all_count(keywords=search_keywords)
        total_count = counts['total']
        
        # 计算总页数
        total_pages = max(1, (total_count + self.results_per_page - 1) // self.results_per_page)
        
        # 执行联合搜索
        # 为了分页，我们需要获取足够多的结果，然后手动分页
        # 因为channels和messages是分开查询的，我们需要合并后再分页
        all_results = await db.search_all(
            keywords=search_keywords,
            limit=1000,  # 获取足够多的结果用于分页
            offset=0
        )
        
        # 将channels转换为类似messages的格式
        formatted_channels = []
        for channel in all_results['channels']:
            # 构建频道元信息格式的content
            channel_content_parts = []
            if channel.get('channel_title'):
                channel_content_parts.append(channel['channel_title'])
            if channel.get('channel_username'):
                channel_content_parts.append(channel['channel_username'])
            if channel.get('category'):
                channel_content_parts.append(f"分类:{channel['category']}")
            if channel.get('member_count'):
                channel_content_parts.append(f"成员:{channel['member_count']}")
            channel_content_parts.append("#资源分享#频道元信息")
            
            channel_dict = {
                'id': channel.get('id'),
                'channel_id': channel.get('id'),
                'message_id': None,
                'storage_message_id': None,
                'content': ' '.join(channel_content_parts),
                'media_type': 'channel',
                'media_url': None,
                'author': None,
                'publish_date': channel.get('discovered_date'),
                'collected_date': channel.get('discovered_date'),
                'channel_username': channel.get('channel_username'),
                'channel_title': channel.get('channel_title'),
                'is_channel': True  # 标识这是频道结果
            }
            formatted_channels.append(channel_dict)
        
        # 合并channels和messages结果
        all_combined = formatted_channels + all_results['messages']
        
        # 按时间排序（最新的在前）
        all_combined.sort(
            key=lambda x: x.get('collected_date') or x.get('publish_date') or '',
            reverse=True
        )
        
        # 应用媒体类型过滤（如果有）
        if filters.get('media_type'):
            all_combined = [
                r for r in all_combined 
                if r.get('media_type') == filters.get('media_type')
            ]
            # 重新计算总数和页数
            total_count = len(all_combined)
            total_pages = max(1, (total_count + self.results_per_page - 1) // self.results_per_page)
        
        # 手动分页
        offset = page * self.results_per_page
        results = all_combined[offset:offset + self.results_per_page]
        
        return results, total_pages, total_count
    
    def _parse_query(self, query: str) -> Tuple[List[str], Dict[str, str]]:
        """
        解析查询字符串，提取关键词和过滤器
        
        支持的语法：
        - 普通关键词: Python 教程
        - 频道过滤: channel:@tech_news
        - 类型过滤: type:video
        - 日期过滤: date:2025-11
        
        Returns:
            (关键词列表, 过滤器字典)
        """
        keywords = []
        filters = {}
        
        # 提取过滤器
        filter_pattern = r'(\w+):([^\s]+)'
        for match in re.finditer(filter_pattern, query):
            key, value = match.group(1), match.group(2)
            filters[key.lower()] = value
            # 从查询中移除过滤器
            query = query.replace(match.group(0), '')
        
        # 剩余的是关键词
        keywords = [kw.strip() for kw in query.split() if kw.strip()]
        
        return keywords, filters
    
    async def get_popular_keywords(self, limit: int = 10) -> List[Dict]:
        """获取热门搜索关键词"""
        # TODO: 实现搜索历史记录和统计
        return []
    
    async def get_related_channels(self, keyword: str, limit: int = 5) -> List[Dict]:
        """根据关键词推荐相关频道"""
        # 在频道标题和备注中搜索
        all_channels = await db.get_all_channels(status='active')
        
        related = []
        keyword_lower = keyword.lower()
        
        for channel in all_channels:
            score = 0
            
            # 检查频道名
            if channel['channel_username'] and keyword_lower in channel['channel_username'].lower():
                score += 3
            
            # 检查频道标题
            if channel['channel_title'] and keyword_lower in channel['channel_title'].lower():
                score += 2
            
            # 检查分类
            if channel['category'] and keyword_lower in channel['category'].lower():
                score += 1
            
            if score > 0:
                channel['relevance_score'] = score
                related.append(channel)
        
        # 按相关度排序
        related.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return related[:limit]
    
    def highlight_keywords(self, text: str, keywords: List[str]) -> str:
        """在文本中高亮显示关键词（用于Telegram格式）"""
        if not keywords or not text:
            return text
        
        # Telegram 支持的格式：*bold* _italic_ `code`
        # 这里使用 *bold* 来高亮
        highlighted = text
        for keyword in keywords:
            # 使用正则表达式，忽略大小写
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            highlighted = pattern.sub(f"*{keyword}*", highlighted)
        
        return highlighted
    
    def format_search_result(self, result: Dict, keywords: List[str] = None, index: int = 1) -> str:
        """格式化单个搜索结果（文字本身就是超链接）"""
        content = result.get('content', '无标题')
        
        # 判断是否是频道元信息
        is_channel_metadata = '#频道元信息' in content or '分类:' in content
        
        # 如果是频道元信息，提取频道名称作为显示内容（不要用户名）
        if is_channel_metadata:
            # 内容格式：频道名称 用户名 分类:xxx 成员:xxx #标签
            channel_title = result.get('channel_title')
            if channel_title:
                display_content = channel_title
            else:
                parts = content.split()
                display_content = parts[0] if parts else content  # 只显示频道名称
        else:
            # 普通消息内容直接使用文本内容（截断即可）
            display_content = content
            max_length = 120
            if len(display_content) > max_length:
                display_content = display_content[:max_length] + "..."
        
        # 转义 Markdown 特殊字符（避免链接格式被破坏）
        display_content = self._escape_markdown_for_link(display_content)
        
        # 获取媒体类型emoji
        media_type = result.get('media_type', 'text')
        
        # 如果是频道元信息，使用频道图标
        if is_channel_metadata:
            media_emoji = "📺"
        else:
            media_emoji = self._get_media_emoji(media_type)
        
        # 构建超链接（如果有存储消息ID）
        storage_message_id = result.get('storage_message_id')
        channel_username = (result.get('channel_username') or '').lstrip('@')
        message_id = result.get('message_id')
        
        # 构建链接URL
        link_url = None
        storage_channel_id = str(config.STORAGE_CHANNEL_ID).replace('-100', '')
        is_private_identifier = channel_username.startswith('c_') if channel_username else False
        
        if is_channel_metadata:
            if channel_username and not is_private_identifier:
                link_url = f"https://t.me/{channel_username}"
            elif storage_message_id:
                link_url = f"https://t.me/c/{storage_channel_id}/{storage_message_id}"
        else:
            if channel_username and not is_private_identifier and message_id:
                link_url = f"https://t.me/{channel_username}/{message_id}"
            elif channel_username and not is_private_identifier:
                link_url = f"https://t.me/{channel_username}"
            elif storage_message_id:
                link_url = f"https://t.me/c/{storage_channel_id}/{storage_message_id}"
        
        # 格式化结果：文字本身就是超链接（Markdown 格式）
        if link_url:
            # 使用 Markdown 超链接格式：[文字](链接)
            formatted = f"{index}{media_emoji} [{display_content}]({link_url})"
        else:
            # 没有链接时，只显示文字
            formatted = f"{index}{media_emoji} {display_content}"
        
        return formatted
    
    def _escape_markdown(self, text: str) -> str:
        """转义 Markdown 特殊字符（用于普通文本）"""
        if not text:
            return text
        
        # Telegram Markdown 特殊字符（所有字符）
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        
        return text
    
    def _escape_markdown_for_link(self, text: str) -> str:
        """转义 Markdown 特殊字符（用于链接文本）
        
        在 [text](url) 格式中，text 部分不能包含 [ 和 ]，否则会破坏链接格式
        其他字符也需要转义，但 (, ) 在 URL 部分，不影响链接文本
        """
        if not text:
            return text
        
        # 链接文本中最危险的字符：[ ] 会破坏链接格式
        # 其他字符也需要转义以保持格式安全
        # 但不需要转义 ( ) 因为这些在 URL 部分
        special_chars = ['_', '*', '[', ']', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        
        return text
    
    def _get_media_emoji(self, media_type: str) -> str:
        """获取媒体类型的 emoji"""
        emoji_map = {
            'photo': '📸',
            'video': '🎬',
            'document': '📎',
            'audio': '🎵',
            'voice': '🎤',
        }
        return emoji_map.get(media_type, '📄')
    
    async def save_search_history(
        self,
        user_id: int,
        query: str,
        results_count: int
    ):
        """保存搜索历史（用于分析热门关键词）"""
        # TODO: 实现搜索历史记录
        pass


# 创建全局搜索引擎实例
search_engine = SearchEngine()

