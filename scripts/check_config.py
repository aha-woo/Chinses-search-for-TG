#!/usr/bin/env python3
"""
配置检查脚本
用于验证 Bot 配置是否正确
"""
import os
import sys
from pathlib import Path


def check_file_exists(file_path, required=True):
    """检查文件是否存在"""
    exists = Path(file_path).exists()
    status = "✅" if exists else ("❌" if required else "⚠️")
    required_text = "(必需)" if required else "(可选)"
    print(f"{status} {file_path} {required_text}")
    return exists


def check_env_variable(var_name, required=True):
    """检查环境变量"""
    from dotenv import load_dotenv
    load_dotenv()
    
    value = os.getenv(var_name)
    has_value = bool(value and value != 'your_' + var_name.lower() + '_here')
    status = "✅" if has_value else ("❌" if required else "⚠️")
    required_text = "(必需)" if required else "(可选)"
    
    if has_value:
        # 隐藏敏感信息
        if 'TOKEN' in var_name or 'HASH' in var_name:
            display_value = value[:10] + "..." if len(value) > 10 else "***"
        else:
            display_value = value
        print(f"{status} {var_name}: {display_value} {required_text}")
    else:
        print(f"{status} {var_name}: 未设置 {required_text}")
    
    return has_value


def main():
    print("=" * 60)
    print("🔍 Telegram 中文搜索 Bot - 配置检查")
    print("=" * 60)
    print()
    
    # 检查必需文件
    print("📁 检查项目文件...")
    print("-" * 60)
    
    required_files = [
        'requirements.txt',
        'config.py',
        'database.py',
        'bot.py',
        'main.py',
        '.env'
    ]
    
    optional_files = [
        'crawler.py',
        'search.py',
        'reports.py',
        'extractor.py'
    ]
    
    all_files_ok = True
    for file in required_files:
        if not check_file_exists(file, required=True):
            all_files_ok = False
    
    for file in optional_files:
        check_file_exists(file, required=False)
    
    print()
    
    # 检查环境变量
    print("⚙️ 检查环境变量配置...")
    print("-" * 60)
    
    if not check_file_exists('.env', required=True):
        print("\n❌ .env 文件不存在！")
        print("💡 请运行: cp env.example .env")
        print("   然后编辑 .env 文件填写配置")
        sys.exit(1)
    
    required_vars = [
        'BOT_TOKEN',
        'ADMIN_IDS',
        'COLLECT_CHANNEL_ID',
    ]
    
    optional_vars = [
        ('API_ID', '启用爬虫时需要'),
        ('API_HASH', '启用爬虫时需要'),
        ('PHONE_NUMBER', '启用爬虫时需要'),
        ('CRAWLER_ENABLED', '爬虫开关'),
    ]
    
    all_vars_ok = True
    for var in required_vars:
        if not check_env_variable(var, required=True):
            all_vars_ok = False
    
    print()
    print("🔧 可选配置:")
    for var, desc in optional_vars:
        has_var = check_env_variable(var, required=False)
        if not has_var:
            print(f"   💡 {desc}")
    
    print()
    
    # 检查 Python 依赖
    print("📦 检查 Python 依赖...")
    print("-" * 60)
    
    try:
        import telegram
        print(f"✅ python-telegram-bot: {telegram.__version__}")
    except ImportError:
        print("❌ python-telegram-bot 未安装")
        all_vars_ok = False
    
    try:
        import telethon
        print(f"✅ telethon: {telethon.__version__}")
    except ImportError:
        print("⚠️ telethon 未安装（启用爬虫时需要）")
    
    try:
        import dotenv
        print("✅ python-dotenv 已安装")
    except ImportError:
        print("❌ python-dotenv 未安装")
        all_vars_ok = False
    
    try:
        import aiosqlite
        print("✅ aiosqlite 已安装")
    except ImportError:
        print("❌ aiosqlite 未安装")
        all_vars_ok = False
    
    print()
    
    # 检查数据目录
    print("💾 检查数据目录...")
    print("-" * 60)
    
    data_dir = Path("data")
    if data_dir.exists():
        print(f"✅ data/ 目录存在")
        
        db_file = data_dir / "channels.db"
        if db_file.exists():
            size = db_file.stat().st_size
            print(f"✅ 数据库文件存在 ({size} 字节)")
        else:
            print("⚠️ 数据库文件不存在")
            print("   💡 运行: python main.py --init-db")
    else:
        print("⚠️ data/ 目录不存在")
        print("   💡 将在首次运行时自动创建")
    
    print()
    
    # 测试 Bot Token
    print("🤖 测试 Bot Token...")
    print("-" * 60)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    bot_token = os.getenv('BOT_TOKEN')
    if bot_token and bot_token != 'your_bot_token_here':
        try:
            import requests
            response = requests.get(
                f"https://api.telegram.org/bot{bot_token}/getMe",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data.get('result', {})
                    print(f"✅ Bot Token 有效")
                    print(f"   Bot 名称: {bot_info.get('first_name')}")
                    print(f"   Bot 用户名: @{bot_info.get('username')}")
                else:
                    print("❌ Bot Token 无效")
                    all_vars_ok = False
            else:
                print(f"❌ API 请求失败 (状态码: {response.status_code})")
                all_vars_ok = False
        except Exception as e:
            print(f"⚠️ 无法测试 Bot Token: {e}")
    else:
        print("⚠️ 跳过（Bot Token 未设置）")
    
    print()
    print("=" * 60)
    
    # 总结
    if all_files_ok and all_vars_ok:
        print("✅ 所有必需配置检查通过！")
        print()
        print("🚀 可以启动 Bot 了:")
        print("   python main.py")
        print()
        print("📖 更多信息请查看:")
        print("   - QUICKSTART.md - 快速启动指南")
        print("   - USAGE.md - 使用说明")
        print("   - DEPLOYMENT.md - 部署文档")
    else:
        print("❌ 配置检查失败，请修复上述问题后重试")
        print()
        print("💡 常见问题:")
        print("   1. 确保已创建 .env 文件: cp env.example .env")
        print("   2. 编辑 .env 填写 Bot Token 等信息")
        print("   3. 安装依赖: pip install -r requirements.txt")
        print("   4. 初始化数据库: python main.py --init-db")
        sys.exit(1)
    
    print("=" * 60)


if __name__ == '__main__':
    main()

