"""
主入口程序
整合所有模块，启动 Bot 和爬虫
"""
import asyncio
import logging
import sys
import argparse
import signal
from pathlib import Path

from config import config
from database import db
from bot import bot
from crawler import crawler


# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


class Application:
    """主应用类"""
    
    def __init__(self):
        self.bot_task = None
        self.crawler_task = None
        self.is_running = False
    
    async def initialize(self):
        """初始化应用"""
        logger.info("🚀 正在初始化应用...")
        
        # 验证配置
        if not config.validate():
            logger.error("❌ 配置验证失败")
            sys.exit(1)
        
        # 初始化数据库
        logger.info("📊 初始化数据库...")
        await db.init_database()
        
        logger.info("✅ 应用初始化完成")
    
    async def start(self):
        """启动应用"""
        self.is_running = True
        
        logger.info("=" * 50)
        logger.info("🤖 Telegram 中文搜索 Bot")
        logger.info("=" * 50)
        
        # 显示配置信息
        logger.info(f"📺 收集频道: {config.COLLECT_CHANNEL_ID}")
        logger.info(f"💾 存储频道: {config.STORAGE_CHANNEL_ID}")
        logger.info(f"👑 管理员数: {len(config.ADMIN_IDS)}")
        logger.info(f"⚙️ 爬虫状态: {'启用' if config.CRAWLER_ENABLED else '禁用'}")
        
        # 初始化
        await self.initialize()
        
        # 启动 Bot
        logger.info("🤖 启动 Telegram Bot...")
        self.bot_task = asyncio.create_task(bot.start())
        
        # 启动爬虫（如果启用）
        crawler_enabled = await db.get_crawler_status()
        if crawler_enabled and config.API_ID and config.API_HASH:
            logger.info("🕷️ 启动爬虫...")
            self.crawler_task = asyncio.create_task(crawler.start())
        else:
            if not crawler_enabled:
                logger.info("⏸️ 爬虫未启用（数据库开关为 false）")
            else:
                logger.info("⏸️ 爬虫未启用（缺少 API 配置）")
        
        logger.info("=" * 50)
        logger.info("✅ 应用已启动，按 Ctrl+C 停止")
        logger.info("=" * 50)
        
        # 等待任务完成
        tasks = [self.bot_task]
        if self.crawler_task:
            tasks.append(self.crawler_task)
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("⏹️ 任务已取消")
    
    async def stop(self):
        """停止应用"""
        if not self.is_running:
            return
        
        logger.info("⏹️ 正在停止应用...")
        self.is_running = False
        
        # 停止 Bot
        if self.bot_task:
            logger.info("⏹️ 停止 Bot...")
            await bot.stop()
            self.bot_task.cancel()
        
        # 停止爬虫
        if self.crawler_task:
            logger.info("⏹️ 停止爬虫...")
            await crawler.stop()
            self.crawler_task.cancel()
        
        logger.info("✅ 应用已停止")
    
    async def init_database_only(self):
        """仅初始化数据库（用于命令行参数）"""
        logger.info("📊 初始化数据库...")
        await db.init_database()
        logger.info("✅ 数据库初始化完成")


# 全局应用实例
app = Application()


def signal_handler(signum, frame):
    """信号处理器（用于优雅退出）"""
    logger.info(f"📥 收到信号 {signum}，准备退出...")
    # 设置停止标志
    app.is_running = False


async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Telegram 中文搜索 Bot')
    parser.add_argument(
        '--init-db',
        action='store_true',
        help='仅初始化数据库后退出'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='1.0.0'
    )
    
    args = parser.parse_args()
    
    # 仅初始化数据库
    if args.init_db:
        await app.init_database_only()
        return
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 启动应用
        await app.start()
        
        # 保持运行直到收到停止信号
        while app.is_running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("⌨️ 收到键盘中断")
    except Exception as e:
        logger.error(f"❌ 应用异常: {e}", exc_info=True)
    finally:
        await app.stop()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 再见！")
    except Exception as e:
        logger.error(f"❌ 致命错误: {e}", exc_info=True)
        sys.exit(1)

