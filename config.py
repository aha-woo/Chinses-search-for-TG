"""
配置管理模块
负责加载环境变量和提供配置访问接口
"""
import os
from typing import List
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """配置类"""
    
    # Bot 配置
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    ADMIN_IDS: List[int] = [
        int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip()
    ]
    
    # 频道配置
    COLLECT_CHANNEL_ID: int = int(os.getenv('COLLECT_CHANNEL_ID', '-1003241208550'))
    STORAGE_CHANNEL_ID: int = int(os.getenv('STORAGE_CHANNEL_ID', '-1003286651502'))
    SEARCH_GROUP_ID: int = int(os.getenv('SEARCH_GROUP_ID', '8068014765'))
    
    # UserBot 配置
    API_ID: int = int(os.getenv('API_ID', '0'))
    API_HASH: str = os.getenv('API_HASH', '')
    PHONE_NUMBER: str = os.getenv('PHONE_NUMBER', '')
    SESSION_NAME: str = os.getenv('SESSION_NAME', 'crawler_session')
    
    # 爬虫开关
    CRAWLER_ENABLED: bool = os.getenv('CRAWLER_ENABLED', 'false').lower() == 'true'
    
    # 数据库配置
    DATABASE_PATH: str = os.getenv('DATABASE_PATH', './data/channels.db')
    
    # 日志配置
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # 爬虫限制配置
    MAX_CHANNELS_PER_DAY: int = int(os.getenv('MAX_CHANNELS_PER_DAY', '10'))
    CRAWL_DELAY_MIN: int = int(os.getenv('CRAWL_DELAY_MIN', '10'))
    CRAWL_DELAY_MAX: int = int(os.getenv('CRAWL_DELAY_MAX', '30'))
    
    # 搜索广告配置
    SEARCH_AD_TEXT: str = os.getenv('SEARCH_AD_TEXT', '💎 发现更多优质内容，关注我们的频道 @your_channel')
    SEARCH_AD_ENABLED: bool = os.getenv('SEARCH_AD_ENABLED', 'true').lower() == 'true'
    RESULTS_PER_PAGE: int = int(os.getenv('RESULTS_PER_PAGE', '10'))
    
    # 频道验证配置
    CHANNEL_VERIFY_DELAY: float = float(os.getenv('CHANNEL_VERIFY_DELAY', '3.0'))  # 每个频道验证间隔（秒）
    CHANNEL_VERIFY_RANDOM_DELAY: float = float(os.getenv('CHANNEL_VERIFY_RANDOM_DELAY', '1.0'))  # 随机延迟范围（秒）
    
    # 存储频道发送配置
    STORAGE_SEND_DELAY: float = float(os.getenv('STORAGE_SEND_DELAY', '2.0'))  # 发送到存储频道的延迟（秒）
    STORAGE_SEND_RANDOM_DELAY: float = float(os.getenv('STORAGE_SEND_RANDOM_DELAY', '0.5'))  # 随机延迟范围（秒）
    
    @classmethod
    def validate(cls) -> bool:
        """验证必要配置是否存在"""
        if not cls.BOT_TOKEN:
            print("错误: BOT_TOKEN 未设置")
            return False
        
        if not cls.ADMIN_IDS:
            print("警告: ADMIN_IDS 未设置，所有用户都可以管理")
        
        if cls.CRAWLER_ENABLED:
            if not cls.API_ID or not cls.API_HASH:
                print("错误: 爬虫已启用但 API_ID 或 API_HASH 未设置")
                return False
            if not cls.PHONE_NUMBER:
                print("警告: PHONE_NUMBER 未设置")
        
        return True
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """检查用户是否是管理员"""
        if not cls.ADMIN_IDS:
            return True  # 如果未设置管理员，所有人都是管理员
        return user_id in cls.ADMIN_IDS
    
    @classmethod
    def get_database_dir(cls) -> str:
        """获取数据库目录"""
        return os.path.dirname(cls.DATABASE_PATH)


# 创建全局配置实例
config = Config()

