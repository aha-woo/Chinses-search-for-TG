#!/bin/bash
# PM2 快速部署脚本

set -e

echo "=================================================="
echo "🚀 Telegram 中文搜索 Bot - PM2 部署脚本"
echo "=================================================="
echo ""

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    echo "📥 正在安装 Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

echo "✅ Node.js 版本: $(node --version)"

# 检查 PM2
if ! command -v pm2 &> /dev/null; then
    echo "📥 正在安装 PM2..."
    sudo npm install -g pm2
fi

echo "✅ PM2 版本: $(pm2 --version)"

# 进入项目目录
cd ~/ChineseSearch

# 创建日志目录
echo "📁 创建日志目录..."
mkdir -p logs

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "❌ .env 文件不存在"
    echo "💡 请先创建 .env 文件: cp env.example .env"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
echo "📦 安装 Python 依赖..."
source venv/bin/activate
pip install -q -r requirements.txt

# 初始化数据库
if [ ! -f "data/channels.db" ]; then
    echo "📊 初始化数据库..."
    python main.py --init-db
fi

# 停止旧进程（如果存在）
if pm2 list | grep -q "telegram-search-bot"; then
    echo "⏹️ 停止旧进程..."
    pm2 stop telegram-search-bot
    pm2 delete telegram-search-bot
fi

# 启动 Bot
echo "🚀 启动 Bot..."
pm2 start ecosystem.config.js

# 保存进程列表
pm2 save

# 设置开机自启（如果还没设置）
if [ ! -f "/etc/systemd/system/pm2-root.service" ]; then
    echo "🔧 设置开机自启..."
    pm2 startup systemd -u root --hp /root
    echo "⚠️ 请执行上面显示的命令以完成设置"
fi

echo ""
echo "=================================================="
echo "✅ 部署完成！"
echo "=================================================="
echo ""
echo "📊 查看状态: pm2 list"
echo "📋 查看日志: pm2 logs telegram-search-bot"
echo "🔄 重启: pm2 restart telegram-search-bot"
echo "⏹️ 停止: pm2 stop telegram-search-bot"
echo ""
echo "📖 详细文档: PM2_GUIDE.md"
echo ""

