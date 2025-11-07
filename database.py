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
import logging

from config import config

logger = logging.getLogger(__name__)


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
                    notes TEXT,
                    description TEXT,
                    photo_file_id TEXT
                )
            """)
            
            # 数据库迁移：为现有表添加新字段（如果不存在）
            try:
                # 检查 description 字段是否存在
                cursor = await conn.execute("PRAGMA table_info(channels)")
                columns = [row[1] for row in await cursor.fetchall()]
                
                if 'description' not in columns:
                    await conn.execute("ALTER TABLE channels ADD COLUMN description TEXT")
                    logger.info("✅ 已添加 description 字段")
                
                if 'photo_file_id' not in columns:
                    await conn.execute("ALTER TABLE channels ADD COLUMN photo_file_id TEXT")
                    logger.info("✅ 已添加 photo_file_id 字段")
            except Exception as e:
                logger.warning(f"⚠️ 数据库迁移可能失败（字段可能已存在）: {e}")
            
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
            
            # 创建搜索历史表（用于热搜功能）
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    query TEXT NOT NULL,
                    results_count INTEGER DEFAULT 0,
                    search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_search_history_query 
                ON search_history(query)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_search_history_date 
                ON search_history(search_date)
            """)
            
            # 创建消息处理进度表（用于断点续传）
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS message_processing_status (
                    message_id TEXT PRIMARY KEY,
                    total_channels INTEGER DEFAULT 0,
                    processed_channels TEXT DEFAULT '',
                    status TEXT DEFAULT 'processing',
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_text TEXT,
                    channel_list TEXT
                )
            """)
            
            # 数据库迁移：为现有表添加新字段（如果不存在）
            try:
                cursor = await conn.execute("PRAGMA table_info(message_processing_status)")
                columns = [row[1] for row in await cursor.fetchall()]
                
                if 'message_text' not in columns:
                    await conn.execute("ALTER TABLE message_processing_status ADD COLUMN message_text TEXT")
                    logger.info("✅ 已添加 message_text 字段")
                
                if 'channel_list' not in columns:
                    await conn.execute("ALTER TABLE message_processing_status ADD COLUMN channel_list TEXT")
                    logger.info("✅ 已添加 channel_list 字段")
            except Exception as e:
                logger.warning(f"⚠️ 数据库迁移可能失败（字段可能已存在）: {e}")
            
            # 创建索引
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_message_status 
                ON message_processing_status(status)
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
        category: str = 'uncategorized',
        description: str = None,
        photo_file_id: str = None
    ) -> Optional[int]:
        """添加频道"""
        async with self.get_connection() as conn:
            try:
                cursor = await conn.execute("""
                    INSERT INTO channels 
                    (channel_username, channel_id, channel_title, channel_type, 
                     discovered_from, category, description, photo_file_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (username, channel_id, title, channel_type, discovered_from, category, description, photo_file_id))
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
    
    async def search_messages_count(
        self,
        keywords: List[str],
        channel_id: int = None,
        media_type: str = None
    ) -> int:
        """搜索消息总数（用于计算分页）"""
        query = """
            SELECT COUNT(*) as count
            FROM messages m
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
        
        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params)
            row = await cursor.fetchone()
            return row['count'] if row else 0
    
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
    
    # ============ 联合搜索 ============
    
    async def search_all(
        self,
        keyword: str = None,
        keywords: List[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, List[Dict]]:
        """
        联合搜索：同时在channels和messages表中搜索关键词
        返回包含channels和messages两个列表的字典
        
        Args:
            keyword: 单个搜索关键词（向后兼容）
            keywords: 多个搜索关键词列表（OR逻辑）
            limit: 每个表返回的最大结果数
            offset: 偏移量
            
        Returns:
            {
                'channels': [...],  # 匹配的频道列表
                'messages': [...]   # 匹配的消息列表
            }
        """
        # 支持单个关键词或关键词列表
        if keywords:
            keyword_list = keywords
        elif keyword:
            keyword_list = [keyword]
        else:
            return {'channels': [], 'messages': []}
        
        if not keyword_list:
            return {'channels': [], 'messages': []}
        
        results = {'channels': [], 'messages': []}
        
        async with self.get_connection() as conn:
            # 构建关键词搜索条件（OR逻辑）
            channel_conditions = []
            message_conditions = []
            channel_params = []
            message_params = []
            
            for kw in keyword_list:
                keyword_pattern = f"%{kw}%"
                # 频道表的搜索条件（每个关键词需要3个参数）
                channel_conditions.append(
                    "(channel_username LIKE ? OR channel_title LIKE ? OR notes LIKE ?)"
                )
                channel_params.extend([keyword_pattern, keyword_pattern, keyword_pattern])
                # 消息表的搜索条件（每个关键词需要1个参数）
                message_conditions.append("m.content LIKE ?")
                message_params.append(keyword_pattern)
            
            # 搜索频道表：在channel_username, channel_title, notes中搜索
            channel_query = f"""
                SELECT * FROM channels
                WHERE ({' OR '.join(channel_conditions)})
                ORDER BY discovered_date DESC
                LIMIT ? OFFSET ?
            """
            channel_params_with_limit = channel_params + [limit, offset]
            cursor = await conn.execute(channel_query, channel_params_with_limit)
            channel_rows = await cursor.fetchall()
            results['channels'] = [dict(row) for row in channel_rows]
            
            # 搜索消息表：在content中搜索
            message_query = f"""
                SELECT m.*, c.channel_username, c.channel_title 
                FROM messages m
                LEFT JOIN channels c ON m.channel_id = c.id
                WHERE ({' OR '.join(message_conditions)})
                ORDER BY m.collected_date DESC
                LIMIT ? OFFSET ?
            """
            message_params_with_limit = message_params + [limit, offset]
            cursor = await conn.execute(message_query, message_params_with_limit)
            message_rows = await cursor.fetchall()
            results['messages'] = [dict(row) for row in message_rows]
        
        return results
    
    async def search_all_count(
        self, 
        keyword: str = None, 
        keywords: List[str] = None
    ) -> Dict[str, int]:
        """
        获取联合搜索的总数
        
        Args:
            keyword: 单个搜索关键词（向后兼容）
            keywords: 多个搜索关键词列表（OR逻辑）
        
        Returns:
            {
                'channels': 频道匹配数量,
                'messages': 消息匹配数量,
                'total': 总匹配数量
            }
        """
        # 支持单个关键词或关键词列表
        if keywords:
            keyword_list = keywords
        elif keyword:
            keyword_list = [keyword]
        else:
            return {'channels': 0, 'messages': 0, 'total': 0}
        
        if not keyword_list:
            return {'channels': 0, 'messages': 0, 'total': 0}
        
        counts = {'channels': 0, 'messages': 0, 'total': 0}
        
        async with self.get_connection() as conn:
            # 构建关键词搜索条件（OR逻辑）
            channel_conditions = []
            message_conditions = []
            channel_params = []
            message_params = []
            
            for kw in keyword_list:
                keyword_pattern = f"%{kw}%"
                # 频道表的搜索条件（每个关键词需要3个参数）
                channel_conditions.append(
                    "(channel_username LIKE ? OR channel_title LIKE ? OR notes LIKE ?)"
                )
                channel_params.extend([keyword_pattern, keyword_pattern, keyword_pattern])
                # 消息表的搜索条件（每个关键词需要1个参数）
                message_conditions.append("content LIKE ?")
                message_params.append(keyword_pattern)
            
            # 统计频道匹配数
            channel_query = f"""
                SELECT COUNT(*) as count FROM channels
                WHERE ({' OR '.join(channel_conditions)})
            """
            cursor = await conn.execute(channel_query, channel_params)
            row = await cursor.fetchone()
            counts['channels'] = row['count'] if row else 0
            
            # 统计消息匹配数
            message_query = f"""
                SELECT COUNT(*) as count FROM messages
                WHERE ({' OR '.join(message_conditions)})
            """
            cursor = await conn.execute(message_query, message_params)
            row = await cursor.fetchone()
            counts['messages'] = row['count'] if row else 0
            
            counts['total'] = counts['channels'] + counts['messages']
        
        return counts
    
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
    
    # ============ 消息处理进度管理（断点续传） ============
    
    async def get_message_processing_status(self, message_id: str) -> Optional[Dict]:
        """获取消息处理状态"""
        async with self.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT * FROM message_processing_status WHERE message_id = ?
            """, (message_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def init_message_processing(
        self, 
        message_id: str, 
        total_channels: int,
        message_text: str = None,
        channel_list: str = None
    ):
        """初始化消息处理状态"""
        async with self.get_connection() as conn:
            await conn.execute("""
                INSERT OR REPLACE INTO message_processing_status 
                (message_id, total_channels, processed_channels, status, started_at, updated_at, message_text, channel_list)
                VALUES (?, ?, '', 'processing', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?)
            """, (message_id, total_channels, message_text, channel_list))
            await conn.commit()
    
    async def mark_channel_processed(self, message_id: str, channel_username: str):
        """标记频道已处理"""
        async with self.get_connection() as conn:
            # 获取当前已处理的频道列表
            cursor = await conn.execute("""
                SELECT processed_channels FROM message_processing_status WHERE message_id = ?
            """, (message_id,))
            row = await cursor.fetchone()
            
            if row:
                processed = row['processed_channels'] or ''
                processed_list = processed.split(',') if processed else []
                
                # 添加新处理的频道（去重）
                if channel_username not in processed_list:
                    processed_list.append(channel_username)
                    processed_str = ','.join(processed_list)
                    
                    # 更新处理进度
                    await conn.execute("""
                        UPDATE message_processing_status 
                        SET processed_channels = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE message_id = ?
                    """, (processed_str, message_id))
                    await conn.commit()
    
    async def get_processed_channels(self, message_id: str) -> set:
        """获取已处理的频道列表"""
        async with self.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT processed_channels FROM message_processing_status WHERE message_id = ?
            """, (message_id,))
            row = await cursor.fetchone()
            
            if row and row['processed_channels']:
                return set(row['processed_channels'].split(','))
            return set()
    
    async def complete_message_processing(self, message_id: str):
        """标记消息处理完成"""
        async with self.get_connection() as conn:
            await conn.execute("""
                UPDATE message_processing_status 
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE message_id = ?
            """, (message_id,))
            await conn.commit()
    
    async def get_incomplete_messages(self) -> List[Dict]:
        """获取未完成处理的消息列表"""
        async with self.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT * FROM message_processing_status 
                WHERE status = 'processing'
                ORDER BY started_at ASC
            """)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def update_message_processing_info(
        self, 
        message_id: str, 
        message_text: str = None, 
        channel_list: str = None
    ):
        """更新消息处理信息（消息文本和频道列表）"""
        async with self.get_connection() as conn:
            updates = []
            params = []
            
            if message_text is not None:
                updates.append("message_text = ?")
                params.append(message_text)
            
            if channel_list is not None:
                updates.append("channel_list = ?")
                params.append(channel_list)
            
            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(message_id)
                
                query = f"""
                    UPDATE message_processing_status 
                    SET {', '.join(updates)}
                    WHERE message_id = ?
                """
                await conn.execute(query, params)
                await conn.commit()
    
    # ============ 搜索历史管理（热搜功能） ============
    
    async def save_search_history(
        self,
        user_id: int,
        query: str,
        results_count: int = 0
    ):
        """保存搜索历史"""
        async with self.get_connection() as conn:
            await conn.execute("""
                INSERT INTO search_history (user_id, query, results_count, search_date)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, query, results_count))
            await conn.commit()
    
    async def get_popular_keywords(
        self,
        limit: int = 10,
        days: int = 7
    ) -> List[Dict]:
        """获取热门搜索关键词（最近N天）"""
        async with self.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT 
                    query,
                    COUNT(*) as search_count,
                    SUM(results_count) as total_results
                FROM search_history
                WHERE search_date >= datetime('now', '-' || ? || ' days')
                GROUP BY query
                ORDER BY search_count DESC, total_results DESC
                LIMIT ?
            """, (days, limit))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_search_statistics(self) -> Dict:
        """获取搜索统计信息"""
        async with self.get_connection() as conn:
            # 总搜索次数
            cursor = await conn.execute("SELECT COUNT(*) as total FROM search_history")
            total_searches = (await cursor.fetchone())['total']
            
            # 唯一关键词数
            cursor = await conn.execute("SELECT COUNT(DISTINCT query) as unique FROM search_history")
            unique_keywords = (await cursor.fetchone())['unique']
            
            # 今日搜索次数
            cursor = await conn.execute("""
                SELECT COUNT(*) as today FROM search_history
                WHERE date(search_date) = date('now')
            """)
            today_searches = (await cursor.fetchone())['today']
            
            return {
                'total_searches': total_searches or 0,
                'unique_keywords': unique_keywords or 0,
                'today_searches': today_searches or 0
            }


# 创建全局数据库实例
db = Database()

