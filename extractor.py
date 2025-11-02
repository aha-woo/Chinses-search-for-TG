"""
链接提取模块
从消息中提取 Telegram 频道/群组链接
"""
import re
from typing import List, Set, Dict, Optional
from dataclasses import dataclass


@dataclass
class ExtractedChannel:
    """提取的频道信息"""
    username: str
    url: str
    channel_type: str  # 'username' or 'id'
    source: str  # 原始文本


class LinkExtractor:
    """链接提取器类"""
    
    # 正则表达式模式
    PATTERNS = {
        'full_url': r'(?:https?://)?t\.me/([a-zA-Z0-9_]{5,32})(?:/\d+)?',
        'username': r'@([a-zA-Z0-9_]{5,32})',
        'private_channel': r't\.me/c/(\d+)',
        'joinchat': r't\.me/joinchat/([a-zA-Z0-9_-]+)',
        'tg_protocol': r'tg://(?:resolve|join)\?(?:domain|invite)=([a-zA-Z0-9_]+)',
    }
    
    # 频道分类关键词
    CATEGORY_KEYWORDS = {
        '新闻资讯': ['新闻', '资讯', 'news', '日报', '快讯', '时事'],
        '科技数码': ['科技', '数码', 'tech', '技术', 'IT', '程序', '编程', 'coding', 'AI', '人工智能'],
        '影视资源': ['电影', '影视', '视频', 'movie', '剧集', '动漫', '番剧', '美剧', '韩剧'],
        '软件工具': ['软件', '工具', 'app', 'software', '破解', 'crack', 'premium'],
        '电子书籍': ['电子书', '书籍', 'book', 'ebook', '小说', '阅读', 'PDF', 'epub'],
        '学习教育': ['教程', '学习', 'tutorial', '课程', 'course', '教育', '考试'],
        '资源分享': ['资源', '分享', 'share', '网盘', 'download', '下载'],
        '娱乐休闲': ['娱乐', '音乐', 'music', '游戏', 'game', '搞笑', '段子'],
        '生活服务': ['生活', '服务', '购物', 'shopping', '美食', '旅游'],
        '金融投资': ['金融', '投资', '股票', 'crypto', '加密货币', 'bitcoin', '交易'],
    }
    
    def __init__(self):
        self.compiled_patterns = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self.PATTERNS.items()
        }
    
    def extract_from_text(self, text: str) -> List[ExtractedChannel]:
        """从文本中提取频道链接"""
        if not text:
            return []
        
        extracted = []
        seen = set()  # 用于去重
        
        # 提取完整 URL
        for match in self.compiled_patterns['full_url'].finditer(text):
            username = match.group(1).lower()
            if username not in seen:
                seen.add(username)
                extracted.append(ExtractedChannel(
                    username=username,
                    url=f"https://t.me/{username}",
                    channel_type='username',
                    source=match.group(0)
                ))
        
        # 提取 @username
        for match in self.compiled_patterns['username'].finditer(text):
            username = match.group(1).lower()
            if username not in seen and self._is_valid_username(username):
                seen.add(username)
                extracted.append(ExtractedChannel(
                    username=username,
                    url=f"https://t.me/{username}",
                    channel_type='username',
                    source=match.group(0)
                ))
        
        # 提取私有频道 ID
        for match in self.compiled_patterns['private_channel'].finditer(text):
            channel_id = match.group(1)
            unique_key = f"c_{channel_id}"
            if unique_key not in seen:
                seen.add(unique_key)
                extracted.append(ExtractedChannel(
                    username=f"c_{channel_id}",
                    url=f"https://t.me/c/{channel_id}",
                    channel_type='id',
                    source=match.group(0)
                ))
        
        # 提取 joinchat 链接
        for match in self.compiled_patterns['joinchat'].finditer(text):
            invite_hash = match.group(1)
            unique_key = f"joinchat_{invite_hash}"
            if unique_key not in seen:
                seen.add(unique_key)
                extracted.append(ExtractedChannel(
                    username=unique_key,
                    url=f"https://t.me/joinchat/{invite_hash}",
                    channel_type='invite',
                    source=match.group(0)
                ))
        
        return extracted
    
    def _is_valid_username(self, username: str) -> bool:
        """验证用户名是否有效"""
        # 过滤掉常见的非频道 @mention
        invalid_keywords = [
            'admin', 'bot', 'support', 'help', 'here', 'all', 'everyone',
            'channel', 'group', 'username'
        ]
        return (
            len(username) >= 5 and 
            username not in invalid_keywords and
            not username.isdigit()
        )
    
    def categorize_channel(self, text: str, title: str = None) -> str:
        """根据文本内容智能分类频道"""
        combined_text = (text or '') + ' ' + (title or '')
        combined_text = combined_text.lower()
        
        # 统计每个分类的关键词匹配数
        category_scores = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword.lower() in combined_text)
            if score > 0:
                category_scores[category] = score
        
        # 返回匹配度最高的分类
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return '其他'
    
    def extract_channel_info_from_message(self, text: str) -> Dict[str, any]:
        """从消息中提取频道信息（包括分类）"""
        channels = self.extract_from_text(text)
        
        if not channels:
            return None
        
        # 取第一个提取的频道
        channel = channels[0]
        
        # 智能分类
        category = self.categorize_channel(text)
        
        return {
            'username': channel.username,
            'url': channel.url,
            'channel_type': channel.channel_type,
            'category': category,
            'source_text': text[:200]  # 保留前200字符作为来源
        }
    
    def batch_extract(self, messages: List[str]) -> List[ExtractedChannel]:
        """批量提取多条消息中的链接"""
        all_channels = []
        seen = set()
        
        for message in messages:
            channels = self.extract_from_text(message)
            for channel in channels:
                if channel.username not in seen:
                    seen.add(channel.username)
                    all_channels.append(channel)
        
        return all_channels
    
    def get_unique_usernames(self, text: str) -> Set[str]:
        """获取文本中的唯一用户名集合"""
        channels = self.extract_from_text(text)
        return {channel.username for channel in channels}


# 创建全局提取器实例
extractor = LinkExtractor()


# 测试函数
def test_extractor():
    """测试提取器功能"""
    test_cases = [
        "推荐一个好频道 @tech_news 里面有很多科技资讯",
        "https://t.me/movie_share 电影资源分享",
        "加入这个群 t.me/joinchat/AaBbCc123",
        "私有频道 https://t.me/c/1234567890/100",
        "多个频道：@news_daily @tech_world https://t.me/book_share",
    ]
    
    print("=== 链接提取器测试 ===\n")
    
    for i, text in enumerate(test_cases, 1):
        print(f"测试 {i}: {text}")
        channels = extractor.extract_from_text(text)
        if channels:
            for channel in channels:
                category = extractor.categorize_channel(text)
                print(f"  ✓ {channel.username} ({channel.channel_type}) - 分类: {category}")
                print(f"    URL: {channel.url}")
        else:
            print("  ✗ 未提取到频道")
        print()


if __name__ == '__main__':
    test_extractor()

