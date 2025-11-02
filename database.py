"""
数据库管理模块
负责数据库初始化、CRUD 操作和查询
"""
import sqlite3
import asyncio
import aiosqlite
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import asynccontextmanager
import os

from config import config


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        data_dir = os.path.dirname(self.db_path)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
    
    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row
        try:
            yield conn
        finally:
            await conn.close()
    
    async def init_database(self):
        """初始化数据库表结构"""
        async with self.get_connection() as conn:
            # 创建频道表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_username TEXT UNIQUE,
                    channel_id TEXT,
                    channel_title TEXT,
                    channel_type TEXT DEFAULT 'channel',
                    discovered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    discovered_from TEXT,
                    category TEXT DEFAULT 'uncategorized',
                    member_count INTEGER DEFAULT 0,
                    is_verified BOOLEAN DEFAULT 0,
                    is_crawling_enabled BOOLEAN DEFAULT 0,
                    last_crawled TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    notes TEXT
                )
            """)
            
            # 创建消息索引表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id INTEGER,
                    message_id TEXT,
                    storage_message_id TEXT,
                    content TEXT,
                    media_type TEXT DEFAULT 'text',
                    media_url TEXT,
                    author TEXT,
                    publish_date TIMESTAMP,
                    collected_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (channel_id) REFERENCES channels(id)
                )
            """)
            
            # 创建配置表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_channels_username 
                ON channels(channel_username)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_channels_status 
                ON channels(status)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_content 
                ON messages(content)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_channel 
                ON messages(channel_id)
            """)
            
            await conn.commit()
            print("✅ 数据库初始化完成")
    
    # ============ 频道操作 ============
    
    async def add_channel(
        self, 
        username: str, 
        channel_id: str = None,
        title: str = None,
        channel_type: str = 'channel',
        discovered_from: str = None,
        category: str = 'uncategorized'
    ) -> Optional[int]:
        """添加频道"""
        async with self.get_connection() as conn:
            try:
                cursor = await conn.execute("""
                    INSERT INTO channels 
                    (channel_username, channel_id, channel_title, channel_type, 
                     discovered_from, category)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (username, channel_id, title, channel_type, discovered_from, category))
                await conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                # 频道已存在
                return None
    
    async def get_channel_by_username(self, username: str) -> Optional[Dict]:
        """根据用户名获取频道"""
        async with self.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT * FROM channels WHERE channel_username = ?
            """, (username,))
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_all_channels(
        self, 
        status: str = None,
        category: str = None,
        limit: int = None,
        offset: int = 0
    ) -> List[Dict]:
        """获取所有频道"""
        query = "SELECT * FROM channels WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY discovered_date DESC"
        
        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        
        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def update_channel(self, channel_id: int, **kwargs):
        """更新频道信息（按数据库ID）"""
        if not kwargs:
            return
        
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        query = f"UPDATE channels SET {set_clause} WHERE id = ?"
        params = list(kwargs.values()) + [channel_id]
        
        async with self.get_connection() as conn:
            await conn.execute(query, params)
            await conn.commit()
    
    async def update_channel_by_username(self, username: str, **kwargs):
        """更新频道信息（按用户名）"""
        if not kwargs:
            return
        
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        query = f"UPDATE channels SET {set_clause} WHERE channel_username = ?"
        params = list(kwargs.values()) + [username]
        
        async with self.get_connection() as conn:
            await conn.execute(query, params)
            await conn.commit()
    
    async def delete_channel(self, channel_id: int):
        """删除频道"""
        async with self.get_connection() as conn:
            await conn.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
            await conn.execute("DELETE FROM messages WHERE channel_id = ?", (channel_id,))
            await conn.commit()
    
    async def get_channels_count(self, status: str = None) -> int:
        """获取频道数量"""
        query = "SELECT COUNT(*) as count FROM channels"
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status)
        
        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params)
            row = await cursor.fetchone()
            return row['count'] if row else 0
    
    async def get_channels_by_category(self) -> Dict[str, int]:
        """按分类统计频道数量"""
        async with self.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT category, COUNT(*) as count 
                FROM channels 
                GROUP BY category
                ORDER BY count DESC
            """)
            rows = await cursor.fetchall()
            return {row['category']: row['count'] for row in rows}
    
    async def get_crawling_enabled_channels(self) -> List[Dict]:
        """获取启用爬取的频道"""
        return await self.get_all_channels(status='active')
    
    # ============ 消息操作 ============
    
    async def add_message(
        self,
        channel_id: int,
        message_id: str,
        content: str,
        media_type: str = 'text',
        media_url: str = None,
        author: str = None,
        publish_date: datetime = None,
        storage_message_id: str = None
    ) -> int:
        """添加消息"""
        async with self.get_connection() as conn:
            cursor = await conn.execute("""
                INSERT INTO messages 
                (channel_id, message_id, content, media_type, media_url, 
                 author, publish_date, storage_message_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (channel_id, message_id, content, media_type, media_url, 
                  author, publish_date, storage_message_id))
            await conn.commit()
            return cursor.lastrowid
    
    async def search_messages(
        self, 
        keywords: List[str],
        channel_id: int = None,
        media_type: str = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict]:
        """搜索消息"""
        query = """
            SELECT m.*, c.channel_username, c.channel_title 
            FROM messages m
            LEFT JOIN channels c ON m.channel_id = c.id
            WHERE 1=1
        """
        params = []
        
        # 关键词搜索
        if keywords:
            conditions = []
            for keyword in keywords:
                conditions.append("m.content LIKE ?")
                params.append(f"%{keyword}%")
            query += f" AND ({' OR '.join(conditions)})"
        
        # 频道过滤
        if channel_id:
            query += " AND m.channel_id = ?"
            params.append(channel_id)
        
        # 媒体类型过滤
        if media_type:
            query += " AND m.media_type = ?"
            params.append(media_type)
        
        query += " ORDER BY m.collected_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_messages_count(self, channel_id: int = None) -> int:
        """获取消息数量"""
        query = "SELECT COUNT(*) as count FROM messages"
        params = []
        
        if channel_id:
            query += " WHERE channel_id = ?"
            params.append(channel_id)
        
        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params)
            row = await cursor.fetchone()
            return row['count'] if row else 0
    
    async def get_messages_by_media_type(self) -> Dict[str, int]:
        """按媒体类型统计消息数量"""
        async with self.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT media_type, COUNT(*) as count 
                FROM messages 
                GROUP BY media_type
                ORDER BY count DESC
            """)
            rows = await cursor.fetchall()
            return {row['media_type']: row['count'] for row in rows}
    
    # ============ 配置操作 ============
    
    async def set_config(self, key: str, value: str):
        """设置配置"""
        async with self.get_connection() as conn:
            await conn.execute("""
                INSERT OR REPLACE INTO config (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value))
            await conn.commit()
    
    async def get_config(self, key: str, default: str = None) -> Optional[str]:
        """获取配置"""
        async with self.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT value FROM config WHERE key = ?
            """, (key,))
            row = await cursor.fetchone()
            return row['value'] if row else default
    
    async def get_crawler_status(self) -> bool:
        """获取爬虫状态"""
        status = await self.get_config('crawler_enabled', 'false')
        return status.lower() == 'true'
    
    async def set_crawler_status(self, enabled: bool):
        """设置爬虫状态"""
        await self.set_config('crawler_enabled', 'true' if enabled else 'false')


# 创建全局数据库实例
db = Database()

