# 🕷️ 爬虫功能启用指南

## 📋 概述

爬虫功能是整个搜索系统的**核心组件**，负责：
1. 自动加入已提取的频道
2. 监听频道中的新消息
3. **将消息转发到 SearchDataStore 频道** （你的数据源）
4. 将消息保存到数据库供搜索
5. 建立中文搜索引擎索引

**当前状态**：❌ 未启用（默认禁用）

---

## ⚠️ 重要警告

### UserBot 风险

爬虫功能使用 **UserBot（Telethon）**，这意味着：

**⚠️ 风险**：
- 使用你的**个人 Telegram 账号**
- 自动加入大量频道可能被识别为机器人行为
- **有封号风险**（临时封禁或永久封禁）
- Telegram 官方不建议自动化操作

**建议**：
- 使用**小号**（不要用主账号）
- 设置合理的加入频率限制
- 定期检查账号状态
- 做好账号被封的心理准备

---

## 🎯 为什么需要 UserBot？

### Bot API vs UserBot

| 功能 | Bot API | UserBot |
|------|---------|---------|
| 发送消息 | ✅ | ✅ |
| 接收消息 | ✅（需要权限） | ✅ |
| 加入频道 | ❌ 不能主动加入 | ✅ 可以 |
| 读取历史消息 | ❌ 需要管理员权限 | ✅ 可以 |
| 自动监听 | ❌ 需要被邀请 | ✅ 可以 |

**结论**：要实现自动爬取频道内容，必须使用 UserBot。

---

## 📝 启用步骤

### 步骤 1：获取 API ID 和 Hash

1. 访问 https://my.telegram.org
2. 用你的手机号登录（建议用小号）
3. 点击 "API development tools"
4. 填写应用信息：
   ```
   App title: ChineseSearchBot
   Short name: csbot
   Platform: Desktop
   Description: Chinese Content Search Engine
   ```
5. 点击 "Create application"
6. 获得：
   ```
   api_id: 12345678
   api_hash: abcdef1234567890abcdef1234567890
   ```

**注意**：这些信息非常重要，请妥善保管！

---

### 步骤 2：配置 .env 文件

在你的 VPS 上：

```bash
cd ~/ChineseSearch
nano .env
```

添加或修改以下内容：

```env
# ============================================
# UserBot 配置
# ============================================

# 从 https://my.telegram.org 获取
API_ID=12345678
API_HASH=your_api_hash_here

# 你的手机号（包含国际区号，如 +86）
PHONE_NUMBER=+8613800138000

# Session 文件名
SESSION_NAME=crawler_session

# ============================================
# 爬虫限制配置（重要！）
# ============================================

# 每天最多加入的频道数（避免触发限制）
MAX_CHANNELS_PER_DAY=10

# 加入频道的延迟范围（秒）
CRAWL_DELAY_MIN=10
CRAWL_DELAY_MAX=30
```

保存退出（Ctrl+X, Y, Enter）

---

### 步骤 3：启用爬虫

有两种方法：

#### 方法 1：使用 Bot 命令（推荐）

在 Telegram 中给你的 Bot 发送：

```
/crawler_status  # 查看当前状态
/crawler_on      # 启用爬虫
```

Bot 会回复：
```
✅ 爬虫已启用

⚠️ 注意: 需要重启 Bot 才能生效
```

#### 方法 2：直接修改数据库

```bash
cd ~/ChineseSearch
sqlite3 data/channels.db
```

```sql
-- 启用爬虫
INSERT OR REPLACE INTO config (key, value) VALUES ('crawler_enabled', 'true');

-- 查看状态
SELECT * FROM config WHERE key = 'crawler_enabled';

-- 退出
.exit
```

---

### 步骤 4：重启 Bot

```bash
pm2 restart telegram-search-bot
```

---

### 步骤 5：首次登录验证

重启后，查看日志：

```bash
pm2 logs telegram-search-bot
```

你会看到：

```
Please enter the code you received: 
```

**这时 Bot 会卡住等待输入验证码**。

#### 获取验证码

1. Telegram 官方会给你的手机号发送验证码
2. 你需要在 VPS 上输入验证码

#### 输入验证码

方法 1：使用 pm2 attach（不推荐，可能不工作）
```bash
pm2 attach telegram-search-bot
# 输入验证码
# Ctrl+C 退出
```

方法 2：临时停止 PM2，手动运行（推荐）
```bash
# 停止 PM2
pm2 stop telegram-search-bot

# 激活虚拟环境
cd ~/ChineseSearch
source venv/bin/activate

# 手动运行（会提示输入验证码）
python main.py
```

输入验证码后，Telegram 会创建 session 文件，以后就不需要再输入了。

看到这个就说明成功：
```
✅ UserBot 已登录: Your Name (@your_username)
🕷️ 启动爬虫...
👂 开始监听频道消息...
```

然后 Ctrl+C 停止，用 PM2 重新启动：
```bash
pm2 restart telegram-search-bot
```

---

## 🔍 验证爬虫是否工作

### 1. 查看日志

```bash
pm2 logs telegram-search-bot
```

应该看到：
```
⚙️ 爬虫状态: 启用
🕷️ 启动爬虫...
✅ UserBot 已登录: Your Name (@your_username)
👂 开始监听频道消息...
🔄 周期性任务：加入新频道
```

### 2. 检查是否加入频道

在 Telegram 中：
- 查看你的账号是否自动加入了之前提取的频道
- 每天最多加入 `MAX_CHANNELS_PER_DAY` 个频道（默认 10 个）

### 3. 检查 SearchDataStore 频道

打开你的 SearchDataStore 频道（-1003286651502）：
- 应该开始有消息被转发进来
- 这些是从已加入频道爬取的消息

### 4. 查看数据库

```bash
sqlite3 data/channels.db
```

```sql
-- 查看已索引的消息数量
SELECT COUNT(*) FROM messages;

-- 查看最新的消息
SELECT * FROM messages ORDER BY created_at DESC LIMIT 10;

-- 退出
.exit
```

---

## 📊 爬虫工作流程

### 1. 启动后立即执行
```
1. 连接 UserBot
2. 获取数据库中 is_crawling_enabled=1 的频道
3. 开始逐个加入频道（有延迟和限制）
```

### 2. 加入频道后
```
1. 监听该频道的新消息
2. 收到新消息 → 转发到 SearchDataStore 频道
3. 保存消息到数据库 messages 表
4. 建立搜索索引
```

### 3. 周期性任务
```
1. 每小时检查是否有新频道需要加入
2. 每天重置加入计数器
3. 健康检查，确保 UserBot 在线
```

---

## ⚙️ 配置参数说明

### 频道加入限制

```env
# 每天最多加入的频道数
MAX_CHANNELS_PER_DAY=10
```

**推荐值**：
- `5` - 非常保守，适合新账号
- `10` - 平衡，推荐 ✅
- `20` - 激进，老账号可以尝试
- `50` - 极度激进，高风险 ⚠️

### 加入延迟

```env
# 加入频道的延迟范围（秒）
CRAWL_DELAY_MIN=10
CRAWL_DELAY_MAX=30
```

**说明**：
- 每次加入频道前会随机等待 10-30 秒
- 避免被识别为机器人行为

**推荐值**：
- 快速：`CRAWL_DELAY_MIN=5, MAX=15`（风险较高）
- 平衡：`CRAWL_DELAY_MIN=10, MAX=30`（推荐）✅
- 安全：`CRAWL_DELAY_MIN=30, MAX=60`（非常慢但安全）

---

## 🐛 常见问题

### Q1: 提示 "FloodWaitError"

**症状**：
```
FloodWaitError: A wait of 3600 seconds is required
```

**原因**：触发了 Telegram 的速率限制

**解决**：
1. 等待指定的时间（这里是 3600 秒 = 1 小时）
2. 降低 `MAX_CHANNELS_PER_DAY`
3. 增加 `CRAWL_DELAY_MIN` 和 `MAX`

### Q2: 账号被封

**症状**：
```
UserDeactivatedBanError: The user has been deleted/deactivated
```

**原因**：账号被 Telegram 封禁

**解决**：
1. 如果是临时封禁，等待解封（通常 24-48 小时）
2. 如果是永久封禁，需要换号
3. 联系 Telegram 官方申诉（成功率低）

**预防**：
- 使用小号
- 降低加入频率
- 设置更长的延迟

### Q3: 爬虫没有加入频道

**检查**：
```bash
# 查看日志
pm2 logs telegram-search-bot | grep "加入频道"

# 检查数据库
sqlite3 data/channels.db
SELECT channel_username, is_crawling_enabled, status 
FROM channels 
WHERE is_crawling_enabled = 1;
```

**可能原因**：
1. 数据库中没有启用爬取的频道
2. 达到每日限制
3. UserBot 没有正常启动

### Q4: SearchDataStore 频道没有消息

**可能原因**：
1. 爬虫刚启动，还没加入频道
2. 已加入的频道没有新消息
3. UserBot 没有权限转发消息

**检查**：
```bash
# 查看是否已加入频道
pm2 logs telegram-search-bot | grep "已加入频道"

# 查看消息数量
sqlite3 data/channels.db
SELECT COUNT(*) FROM messages;
```

### Q5: Session 文件丢失

**症状**：每次重启都要输入验证码

**原因**：`crawler_session.session` 文件丢失或损坏

**解决**：
1. 检查文件是否存在：`ls ~/ChineseSearch/crawler_session.session`
2. 如果不存在，需要重新登录（输入验证码）
3. 备份 session 文件，防止丢失

---

## 📈 性能和限制

### Telegram 限制

| 操作 | 限制 |
|------|------|
| 加入频道 | 约 20-50 个/天（取决于账号年龄） |
| 发送消息 | 约 30 条/秒 |
| 转发消息 | 约 20 条/秒 |
| API 请求 | 约 20 次/秒 |

### 我们的保守设置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 每天加入频道 | 10 | 远低于限制 |
| 加入延迟 | 10-30 秒 | 足够安全 |
| 消息转发 | 实时 | 不会触发限制 |

### 预计时间

假设：
- 已提取 100 个频道
- 每天加入 10 个
- 每个频道平均 100 条消息/天

**时间线**：
- Day 1-10：逐步加入 100 个频道（每天 10 个）
- Day 11+：开始大量收集消息（约 10,000 条/天）
- 1 个月后：数据库约有 30 万条消息

---

## 🎯 最佳实践

### 1. 使用小号

不要用你的主账号，专门注册一个小号用于爬虫。

### 2. 逐步增加

- 第 1 周：`MAX_CHANNELS_PER_DAY=5`
- 第 2 周：如果没问题，增加到 `10`
- 第 3 周：如果没问题，增加到 `15`

### 3. 监控日志

定期检查：
```bash
pm2 logs telegram-search-bot | grep -i "flood\|error\|ban"
```

如果看到 "flood" 或 "ban"，立即降低频率。

### 4. 备份 Session

```bash
# 备份
cp ~/ChineseSearch/crawler_session.session ~/session_backup.session

# 恢复（如果丢失）
cp ~/session_backup.session ~/ChineseSearch/crawler_session.session
```

### 5. 定期检查账号状态

在 Telegram 中：
- 检查账号是否能正常发送消息
- 检查是否收到官方警告
- 检查是否被限制加入频道

---

## 🔄 禁用爬虫

如果想临时或永久禁用爬虫：

### 方法 1：使用 Bot 命令

```
/crawler_off
```

### 方法 2：修改数据库

```bash
sqlite3 data/channels.db
```

```sql
UPDATE config SET value = 'false' WHERE key = 'crawler_enabled';
.exit
```

### 方法 3：修改配置文件

```bash
nano .env
```

删除或注释掉：
```env
# API_ID=12345678
# API_HASH=your_api_hash_here
```

然后重启：
```bash
pm2 restart telegram-search-bot
```

---

## 📞 总结

### 启用爬虫的完整步骤

1. ⚠️ 准备一个小号（不要用主账号）
2. 🔑 获取 API ID 和 Hash（https://my.telegram.org）
3. ⚙️ 配置 .env 文件
4. ✅ 启用爬虫（/crawler_on 或修改数据库）
5. 🔄 重启 Bot
6. 📱 首次登录输入验证码
7. 🔍 验证是否正常工作
8. 📊 等待数据积累

### 是否应该启用？

**需要启用**，如果你想：
- ✅ 将内容存储到 SearchDataStore 频道
- ✅ 使用搜索功能
- ✅ 建立中文内容索引

**可以不启用**，如果你只想：
- 提取频道链接
- 查看频道列表
- 统计频道信息

### 风险提示

- ⚠️ 使用 UserBot 有封号风险
- ⚠️ 建议使用小号
- ⚠️ 设置保守的参数
- ⚠️ 定期监控日志和账号状态

---

**记住**：爬虫是可选功能，但如果你想要完整的搜索引擎功能，就必须启用它！🕷️

