# 快速启动指南

最快 5 分钟让你的 Bot 运行起来！

## 前提条件

- ✅ 已有 VPS（Linux）
- ✅ 已安装 Python 3.9+
- ✅ 已获取 Bot Token（从 @BotFather）
- ✅ 已创建私有频道并获取 ID

## 5 步启动

### 1️⃣ 上传项目到 VPS

```bash
cd ~
# 将项目文件上传到这个目录
```

### 2️⃣ 安装依赖

```bash
cd chinese-search-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3️⃣ 配置环境变量

```bash
cp env.example .env
nano .env
```

**最少配置这 3 项：**

```env
BOT_TOKEN=你的Bot_Token
ADMIN_IDS=你的用户ID
COLLECT_CHANNEL_ID=-1003241208550
```

保存: `Ctrl+O` → `Enter` → `Ctrl+X`

### 4️⃣ 初始化数据库

```bash
python main.py --init-db
```

### 5️⃣ 启动 Bot

```bash
python main.py
```

看到 `✅ Bot 已启动并运行` 就成功了！

在 Telegram 中给 Bot 发送 `/start` 测试。

## 后台运行

按 `Ctrl+C` 停止前台运行，然后：

```bash
nohup python main.py > bot.log 2>&1 &
```

## 查看日志

```bash
tail -f bot.log
```

## 停止 Bot

```bash
pkill -f "python main.py"
```

---

## 进阶配置（可选）

### 配置为系统服务

```bash
# 编辑服务文件中的路径
nano telegram-search-bot.service

# 安装服务
sudo cp telegram-search-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start telegram-search-bot
sudo systemctl enable telegram-search-bot

# 查看状态
sudo systemctl status telegram-search-bot

# 查看日志
sudo journalctl -u telegram-search-bot -f
```

### 启用爬虫功能

1. **配置 API 凭证**（从 https://my.telegram.org 获取）：

```bash
nano .env
```

添加：

```env
API_ID=12345678
API_HASH=你的API_Hash
PHONE_NUMBER=+1234567890
```

2. **首次登录**（需要输入验证码）：

```bash
python main.py
# 按提示输入验证码
# Ctrl+C 停止
```

3. **启用爬虫**：

在 Telegram 中发送：

```
/crawler_on
```

4. **重启 Bot**

---

## 使用 Bot

### 收集频道

将包含频道链接的消息转发到你的私有频道（ID: -1003241208550），Bot 会自动提取。

### 查看统计

```
/stats
```

### 查看收集的频道

```
/channels
```

### 搜索内容（启用爬虫后）

```
/search Python教程
```

---

## 常见问题

**Q: Bot 启动失败？**

```bash
# 检查 Token
cat .env | grep BOT_TOKEN

# 测试网络
curl https://api.telegram.org/bot你的Token/getMe
```

**Q: 无法连接数据库？**

```bash
# 确保 data 目录存在
mkdir -p data

# 重新初始化
python main.py --init-db
```

**Q: 找不到私有频道 ID？**

在频道中转发消息给 @userinfobot，查看返回的 ID。

---

## 下一步

- 📖 阅读 [USAGE.md](USAGE.md) 了解详细功能
- 🚀 阅读 [DEPLOYMENT.md](DEPLOYMENT.md) 了解生产部署
- 💡 查看 [README.md](README.md) 了解项目全貌

---

**开始享受你的 Bot 吧！🎉**

