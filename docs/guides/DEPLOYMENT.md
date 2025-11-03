# 部署指南

本文档详细说明如何在 Linux VPS 上部署 Telegram 中文搜索 Bot。

## 系统要求

- **操作系统**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **Python**: 3.9 或更高版本（已测试 3.12.3）
- **内存**: 至少 512MB RAM
- **磁盘**: 至少 1GB 可用空间
- **网络**: 能够访问 Telegram API

## 准备工作

### 1. 获取 Bot Token

1. 在 Telegram 中找到 @BotFather
2. 发送 `/newbot` 创建新 Bot
3. 按提示设置 Bot 名称和用户名
4. 保存返回的 Token（格式: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`）

### 2. 获取你的用户 ID

1. 在 Telegram 中找到 @userinfobot
2. 发送任意消息
3. 记录返回的用户 ID（纯数字）

### 3. 创建私有频道

1. 在 Telegram 创建一个新频道
2. 设置为私有频道
3. 将你的 Bot 添加为频道管理员
4. 获取频道 ID：
   - 方法 1: 使用 @userinfobot 转发频道消息
   - 方法 2: 在代码中打印 `update.effective_chat.id`

### 4. 获取 API ID/Hash（可选，启用爬虫时需要）

1. 访问 https://my.telegram.org
2. 登录你的 Telegram 账号
3. 点击 "API development tools"
4. 填写应用信息：
   - App title: `Chinese Search Bot`
   - Short name: `search_bot`
   - Platform: `Other`
5. 获得 `api_id` 和 `api_hash`

## 安装步骤

### 1. 连接到 VPS

```bash
ssh your_username@your_server_ip
```

### 2. 更新系统

```bash
sudo apt update
sudo apt upgrade -y
```

### 3. 安装 Python 3.9+

```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip python3-venv -y

# 检查版本
python3 --version
```

### 4. 安装 SQLite（通常已预装）

```bash
sudo apt install sqlite3 -y
```

### 5. 克隆或上传项目

**方法 1: 使用 Git**

```bash
cd ~
git clone <your_repository_url> chinese-search-bot
cd chinese-search-bot
```

**方法 2: 手动上传**

```bash
# 在本地打包
tar -czf chinese-search-bot.tar.gz chinese-search-bot/

# 上传到服务器
scp chinese-search-bot.tar.gz your_username@your_server_ip:~

# 在服务器上解压
cd ~
tar -xzf chinese-search-bot.tar.gz
cd chinese-search-bot
```

### 6. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
```

### 7. 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 8. 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置文件
nano .env
```

**填写以下必填项**:

```env
# Bot 配置
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_IDS=123456789

# 频道配置
COLLECT_CHANNEL_ID=-1003241208550
STORAGE_CHANNEL_ID=-1003241208550

# 爬虫开关（暂时设为 false）
CRAWLER_ENABLED=false
```

**如果要启用爬虫，额外配置**:

```env
# UserBot 配置
API_ID=12345678
API_HASH=abcdef1234567890abcdef
PHONE_NUMBER=+1234567890
```

保存文件: `Ctrl+O` -> `Enter` -> `Ctrl+X`

### 9. 初始化数据库

```bash
python main.py --init-db
```

应该看到输出: `✅ 数据库初始化完成`

### 10. 测试运行

```bash
python main.py
```

应该看到:

```
🤖 正在启动 Bot...
✅ 数据库初始化完成
✅ Bot 已启动并运行
```

在 Telegram 中给你的 Bot 发送 `/start`，确认 Bot 正常响应。

如果正常，按 `Ctrl+C` 停止。

## 配置为系统服务

使用 systemd 让 Bot 在后台持续运行。

### 1. 编辑服务文件

```bash
nano telegram-search-bot.service
```

修改以下内容:

```ini
User=your_actual_username
WorkingDirectory=/home/your_username/chinese-search-bot
Environment="PATH=/home/your_username/chinese-search-bot/venv/bin"
ExecStart=/home/your_username/chinese-search-bot/venv/bin/python main.py
```

### 2. 复制服务文件

```bash
sudo cp telegram-search-bot.service /etc/systemd/system/
```

### 3. 重新加载 systemd

```bash
sudo systemctl daemon-reload
```

### 4. 启动服务

```bash
sudo systemctl start telegram-search-bot
```

### 5. 查看状态

```bash
sudo systemctl status telegram-search-bot
```

应该看到 `Active: active (running)`

### 6. 设置开机自启

```bash
sudo systemctl enable telegram-search-bot
```

## 日常管理

### 查看日志

```bash
# 实时日志
sudo journalctl -u telegram-search-bot -f

# 最近100行
sudo journalctl -u telegram-search-bot -n 100

# 或查看文件日志
tail -f ~/chinese-search-bot/bot.log
```

### 重启服务

```bash
sudo systemctl restart telegram-search-bot
```

### 停止服务

```bash
sudo systemctl stop telegram-search-bot
```

### 更新代码

```bash
# 停止服务
sudo systemctl stop telegram-search-bot

# 更新代码
cd ~/chinese-search-bot
git pull  # 或重新上传文件

# 更新依赖（如果有变化）
source venv/bin/activate
pip install -r requirements.txt

# 重启服务
sudo systemctl start telegram-search-bot
```

## 启用爬虫功能

### 1. 配置 API 凭证

```bash
cd ~/chinese-search-bot
nano .env
```

添加/修改:

```env
API_ID=12345678
API_HASH=your_api_hash
PHONE_NUMBER=+1234567890
```

### 2. 首次登录 Telethon

爬虫首次运行需要手机验证码登录。

```bash
# 临时停止服务
sudo systemctl stop telegram-search-bot

# 手动运行一次（会提示输入验证码）
cd ~/chinese-search-bot
source venv/bin/activate
python main.py
```

按提示输入手机收到的验证码，登录成功后会生成 `.session` 文件。

按 `Ctrl+C` 停止。

### 3. 启用爬虫

在 Telegram 中给你的 Bot 发送:

```
/crawler_on
```

### 4. 重启服务

```bash
sudo systemctl start telegram-search-bot
```

### 5. 验证爬虫运行

```bash
sudo journalctl -u telegram-search-bot -f | grep "爬虫"
```

应该看到: `✅ UserBot 已登录` 和 `🚀 爬虫已启动`

## 数据备份

### 备份数据库

```bash
# 创建备份目录
mkdir -p ~/backups

# 备份数据库
cp ~/chinese-search-bot/data/channels.db ~/backups/channels.db.$(date +%Y%m%d)

# 自动化备份（添加到 crontab）
crontab -e

# 添加这一行（每天凌晨3点备份）
0 3 * * * cp ~/chinese-search-bot/data/channels.db ~/backups/channels.db.$(date +\%Y\%m\%d)
```

### 备份配置

```bash
cp ~/chinese-search-bot/.env ~/backups/.env.backup
```

## 安全建议

### 1. 保护配置文件

```bash
chmod 600 ~/.env
chmod 600 ~/chinese-search-bot/.env
```

### 2. 使用防火墙

```bash
# 安装 UFW
sudo apt install ufw -y

# 允许 SSH
sudo ufw allow 22/tcp

# 启用防火墙
sudo ufw enable
```

### 3. 定期更新系统

```bash
sudo apt update && sudo apt upgrade -y
```

### 4. 使用小号运行爬虫

- 不要使用主账号的 API 凭证
- 专门注册一个新账号用于爬取

## 故障排查

### Bot 无法启动

```bash
# 查看错误日志
sudo journalctl -u telegram-search-bot -n 50

# 检查配置
cat ~/.env

# 测试 Bot Token
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe
```

### 数据库错误

```bash
# 检查数据库文件
ls -lh ~/chinese-search-bot/data/channels.db

# 重新初始化（警告：会清空数据）
rm ~/chinese-search-bot/data/channels.db
python ~/chinese-search-bot/main.py --init-db
```

### 爬虫无法连接

```bash
# 检查 session 文件
ls -lh ~/chinese-search-bot/*.session

# 重新登录
rm ~/chinese-search-bot/*.session
# 然后按照"启用爬虫功能"步骤重新登录
```

### 内存不足

```bash
# 查看内存使用
free -h

# 创建 swap（如果内存<1GB）
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 永久启用
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 性能优化

### 数据库优化

```bash
# 定期优化数据库
sqlite3 ~/chinese-search-bot/data/channels.db "VACUUM;"
```

### 日志轮转

```bash
# 创建 logrotate 配置
sudo nano /etc/logrotate.d/telegram-search-bot
```

内容:

```
/home/your_username/chinese-search-bot/bot.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

## 监控与告警

### 使用 Telegram 发送告警

Bot 可以在出错时给管理员发送消息（功能已内置）。

### 外部监控

可以使用 `uptimerobot.com` 等服务监控 Bot 是否在线。

## 联系支持

如有问题，请通过以下方式联系:

- Telegram Bot: @jisousearchhelp_bot
- GitHub Issues: (your repository)

---

**部署完成！享受你的 Telegram 中文搜索 Bot 🎉**

