# Telegram 中文搜索 Bot

一个功能强大的 Telegram Bot，用于收集、索引和搜索中文频道内容。

## 功能特点

### 核心功能
- ✅ 自动提取消息中的频道/群组链接
- ✅ 智能分类和管理频道
- ✅ 强大的搜索功能
- ✅ 详细的统计报表
- ✅ UserBot 爬取功能（可选启用）

### 功能模块

#### 1. 频道收集
- 监听私有频道消息
- 自动提取 TG 链接（支持多种格式）
- 去重和分类管理
- 频道状态追踪

#### 2. 搜索引擎
- 全文关键词搜索
- 多关键词支持
- 高级过滤（类型、频道、日期）
- 分页显示结果

#### 3. 统计报表
- 总体统计数据
- 频道列表（分类显示）
- 分类统计图表
- 活跃度排名

#### 4. UserBot 爬取（可选）
- 自动加入频道
- 监听新消息
- 转发到私有存储频道
- 建立搜索索引
- **默认禁用，通过开关控制**

## 快速开始

### 1. 环境要求
- Python 3.9+（推荐 3.12）
- SQLite 3
- Linux VPS（推荐）

### 2. 安装依赖

```bash
# 克隆项目
git clone <repository_url>
cd chinese-search-bot

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置

```bash
# 复制配置文件
cp .env.example .env

# 编辑配置文件
nano .env
```

**必填配置：**
```env
BOT_TOKEN=你的Bot Token（从 @BotFather 获取）
ADMIN_IDS=你的用户ID（多个用逗号分隔）
COLLECT_CHANNEL_ID=-1003241208550
STORAGE_CHANNEL_ID=-1003241208550
```

**可选配置（启用爬虫功能时需要）：**
```env
API_ID=12345678
API_HASH=你的API Hash
PHONE_NUMBER=+1234567890
CRAWLER_ENABLED=false
```

### 4. 初始化数据库

```bash
python main.py --init-db
```

### 5. 运行 Bot

```bash
# 前台运行（测试用）
python main.py

# 后台运行方式 1: 使用 PM2（推荐）
sudo npm install -g pm2
pm2 start ecosystem.config.js
pm2 save

# 后台运行方式 2: 使用 nohup
nohup python main.py > bot.log 2>&1 &

# 后台运行方式 3: 使用 systemd
sudo cp telegram-search-bot.service /etc/systemd/system/
sudo systemctl enable telegram-search-bot
sudo systemctl start telegram-search-bot
```

📖 **进程管理**: 查看 [PM2_GUIDE.md](PM2_GUIDE.md)

## 使用指南

### 管理员命令

| 命令 | 功能 |
|------|------|
| `/start` | 启动 Bot，显示欢迎信息 |
| `/help` | 显示帮助文档 |
| `/stats` | 查看统计数据 |
| `/channels` | 频道列表（按钮界面） |
| `/report` | 详细报表 |
| `/search <关键词>` | 搜索内容 |
| `/crawler_status` | 查看爬虫状态 |
| `/crawler_on` | 启用爬虫 |
| `/crawler_off` | 禁用爬虫 |
| `/add_channel <链接>` | 手动添加频道 |

### 工作流程

#### 阶段1：频道收集
1. 将想监控的频道链接转发到私有频道 `Channelcollect_jisou`
2. Bot 自动提取链接并存入数据库
3. 使用 `/channels` 查看收集的频道

#### 阶段2：启用爬虫（可选）
1. 配置 `.env` 文件中的 API_ID、API_HASH
2. 执行 `/crawler_on` 启用爬虫
3. Bot 自动加入频道并开始索引内容

#### 阶段3：搜索使用
1. 用户使用 `/search 关键词` 搜索
2. Bot 返回匹配结果
3. 点击链接直达原文

## 数据库结构

### channels 表
存储频道信息、分类、状态

### messages 表
存储消息索引、内容、媒体类型

### config 表
存储系统配置（如爬虫开关状态）

## 部署建议

### 1. 使用 systemd 服务
```bash
sudo systemctl enable telegram-search-bot
sudo systemctl start telegram-search-bot
```

### 2. 日志管理
```bash
# 查看日志
sudo journalctl -u telegram-search-bot -f

# 或使用文件日志
tail -f bot.log
```

### 3. 数据备份
```bash
# 定期备份数据库
cp data/channels.db data/channels.db.backup.$(date +%Y%m%d)
```

## 安全建议

1. **保护配置文件**
   ```bash
   chmod 600 .env
   ```

2. **使用小号运行 UserBot**
   - 不要用主号的 API 凭证
   - 专门注册一个账号用于爬取

3. **限制管理员权限**
   - 在 `.env` 中正确设置 `ADMIN_IDS`
   - 只有管理员能执行敏感操作

4. **防止滥用**
   - 设置搜索频率限制
   - 监控异常行为

## 风险提示

### UserBot 使用风险
- 大规模爬取可能导致账号被限制
- 建议：
  - 使用专用小号
  - 谨慎控制爬取速度
  - 避免加入太多频道（建议每天<10个）

### 合规性
- 只爬取公开内容
- 尊重频道版权
- 遵守 Telegram 服务条款

## 故障排查

### Bot 无法启动
```bash
# 检查配置
cat .env

# 检查依赖
pip list | grep telegram

# 查看错误日志
tail -n 50 bot.log
```

### 爬虫无法工作
```bash
# 检查爬虫状态
# 在 Telegram 中发送 /crawler_status

# 检查 API 配置
grep -E "API_ID|API_HASH" .env

# 手动测试 Telethon 连接
python -c "from telethon.sync import TelegramClient; print('OK')"
```

### 数据库错误
```bash
# 检查数据库文件
ls -lh data/channels.db

# 重新初始化（警告：会清空数据）
rm data/channels.db
python main.py --init-db
```

## 更新日志

### v1.0.0 (2025-11-02)
- ✅ 初始版本
- ✅ 频道链接提取
- ✅ 搜索功能
- ✅ 统计报表
- ✅ UserBot 爬取（可选）

## 许可证

MIT License

## 联系方式

如有问题，请通过以下方式联系：
- Telegram: @jisousearchhelp_bot
- Issues: GitHub Issues

## 贡献

欢迎提交 Pull Request 或报告 Bug！

