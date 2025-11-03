# 项目结构说明

本文档详细说明项目的文件结构和各模块功能。

## 📁 目录结构

```
chinese-search-bot/
├── 📄 核心模块
│   ├── main.py                    # 主入口程序
│   ├── config.py                  # 配置管理
│   ├── database.py                # 数据库操作
│   ├── bot.py                     # Bot 交互逻辑
│   ├── crawler.py                 # UserBot 爬虫
│   ├── search.py                  # 搜索引擎
│   ├── reports.py                 # 报表生成
│   └── extractor.py               # 链接提取器
│
├── 📝 文档
│   ├── README.md                  # 项目说明
│   ├── QUICKSTART.md              # 快速启动指南
│   ├── USAGE.md                   # 使用说明
│   ├── DEPLOYMENT.md              # 部署文档
│   └── PROJECT_STRUCTURE.md       # 本文件
│
├── ⚙️ 配置文件
│   ├── .env                       # 环境变量（不提交）
│   ├── env.example                # 环境变量示例
│   ├── requirements.txt           # Python 依赖
│   └── .gitignore                 # Git 忽略规则
│
├── 🔧 工具脚本
│   ├── check_config.py            # 配置检查脚本
│   └── telegram-search-bot.service # systemd 服务配置
│
└── 💾 数据目录
    └── data/
        └── channels.db            # SQLite 数据库

```

---

## 📄 核心模块详解

### main.py
**主入口程序**

- 启动和停止应用
- 初始化数据库
- 管理 Bot 和爬虫进程
- 信号处理和优雅退出
- 命令行参数处理

**关键函数:**
- `main()` - 主函数
- `Application.start()` - 启动应用
- `Application.stop()` - 停止应用

**命令行参数:**
```bash
python main.py              # 正常启动
python main.py --init-db    # 仅初始化数据库
python main.py --version    # 显示版本
```

---

### config.py
**配置管理模块**

- 从 `.env` 加载环境变量
- 提供配置访问接口
- 验证配置完整性
- 权限管理（管理员检查）

**主要类:**
- `Config` - 配置类

**环境变量:**
- `BOT_TOKEN` - Bot Token
- `ADMIN_IDS` - 管理员 ID 列表
- `COLLECT_CHANNEL_ID` - 收集频道 ID
- `STORAGE_CHANNEL_ID` - 存储频道 ID
- `API_ID` / `API_HASH` - Telegram API 凭证
- `CRAWLER_ENABLED` - 爬虫开关

---

### database.py
**数据库操作模块**

使用 SQLite + aiosqlite 实现异步数据库操作。

**数据表:**

1. **channels** - 频道信息表
   - `id` - 主键
   - `channel_username` - 频道用户名
   - `channel_title` - 频道标题
   - `category` - 分类
   - `status` - 状态（pending/active/failed）
   - `discovered_date` - 发现时间

2. **messages** - 消息索引表
   - `id` - 主键
   - `channel_id` - 关联频道
   - `content` - 消息内容
   - `media_type` - 媒体类型
   - `publish_date` - 发布时间
   - `storage_message_id` - 存储消息 ID

3. **config** - 系统配置表
   - `key` - 配置键
   - `value` - 配置值

**主要方法:**
- `init_database()` - 初始化数据库
- `add_channel()` - 添加频道
- `get_channel_by_username()` - 获取频道
- `search_messages()` - 搜索消息
- `get_crawler_status()` - 获取爬虫状态

---

### bot.py
**Bot 交互逻辑**

使用 python-telegram-bot 处理用户交互。

**命令处理器:**
- `/start` - 启动 Bot
- `/help` - 帮助信息
- `/stats` - 统计数据
- `/channels` - 频道列表
- `/search` - 搜索
- `/crawler_status` - 爬虫状态
- `/crawler_on` / `/crawler_off` - 控制爬虫

**消息处理器:**
- `handle_channel_message()` - 监听私有频道，提取链接

**回调处理器:**
- `handle_callback()` - 处理按钮点击

**主要类:**
- `TelegramBot` - Bot 主类

---

### crawler.py
**UserBot 爬虫模块**

使用 Telethon 实现频道内容爬取。

**功能:**
- 自动加入频道
- 监听新消息
- 转发到存储频道
- 建立搜索索引
- 限流保护

**安全措施:**
- 每天最多加入 10 个频道
- 随机延迟 10-30 秒
- 捕获 FloodWait 错误
- 健康检查

**主要类:**
- `ChannelCrawler` - 爬虫类

**⚠️ 注意:**
- 需要 API ID/Hash
- 默认禁用，通过开关控制
- 建议使用专用小号

---

### search.py
**搜索引擎模块**

提供全文搜索功能。

**功能:**
- 关键词搜索
- 多关键词支持
- 高级过滤（频道、类型、日期）
- 结果格式化
- 关键词高亮

**搜索语法:**
```
Python                           # 基础搜索
Python type:video                # 类型过滤
Python channel:@tech             # 频道过滤
Python date:2025-11              # 日期过滤
```

**主要类:**
- `SearchEngine` - 搜索引擎类

---

### reports.py
**报表生成模块**

生成各类统计报表。

**报表类型:**
1. 总体统计 - 频道数、消息数、爬虫状态
2. 频道列表 - 分页显示所有频道
3. 分类统计 - 按分类统计频道数量
4. 热门频道 - 按消息数量排名

**主要类:**
- `ReportGenerator` - 报表生成器

---

### extractor.py
**链接提取模块**

从文本中提取 Telegram 频道链接。

**支持格式:**
- `@channel_name`
- `https://t.me/channel_name`
- `t.me/channel_name`
- `t.me/c/1234567890` (私有频道)
- `t.me/joinchat/xxxxx` (邀请链接)

**智能分类:**
根据频道名称和描述自动分类：
- 新闻资讯、科技数码、影视资源
- 软件工具、电子书籍、学习教育
- 资源分享、娱乐休闲等

**主要类:**
- `LinkExtractor` - 链接提取器
- `ExtractedChannel` - 提取的频道信息

---

## ⚙️ 配置文件

### .env
**环境变量配置文件**（实际配置，不提交 Git）

包含敏感信息：
- Bot Token
- API 凭证
- 频道 ID

**安全建议:**
```bash
chmod 600 .env  # 设置文件权限
```

### env.example
**环境变量示例**（提交 Git）

提供配置模板，用户复制后修改。

### requirements.txt
**Python 依赖包列表**

主要依赖：
- `python-telegram-bot==20.7` - Bot 框架
- `telethon==1.34.0` - UserBot 框架
- `python-dotenv==1.0.0` - 环境变量
- `aiosqlite==0.19.0` - 异步 SQLite

安装：
```bash
pip install -r requirements.txt
```

---

## 🔧 工具脚本

### check_config.py
**配置检查脚本**

运行前检查配置是否完整：

```bash
python check_config.py
```

检查项目：
- ✅ 必需文件存在
- ✅ 环境变量配置
- ✅ Python 依赖安装
- ✅ Bot Token 有效性
- ✅ 数据库文件

### telegram-search-bot.service
**systemd 服务配置**

用于将 Bot 配置为系统服务：

```bash
sudo cp telegram-search-bot.service /etc/systemd/system/
sudo systemctl enable telegram-search-bot
sudo systemctl start telegram-search-bot
```

---

## 💾 数据目录

### data/channels.db
**SQLite 数据库文件**

存储所有数据：
- 频道信息
- 消息索引
- 系统配置

**备份建议:**
```bash
# 每天备份
cp data/channels.db backups/channels.db.$(date +%Y%m%d)
```

---

## 📝 文档说明

### README.md
**项目总览**

- 项目介绍
- 功能特点
- 快速开始
- 技术架构

### QUICKSTART.md
**快速启动指南**

- 5 步启动
- 最小配置
- 常见问题

### USAGE.md
**使用说明**

- 详细功能介绍
- 命令用法
- 搜索语法
- 技巧与最佳实践

### DEPLOYMENT.md
**部署文档**

- 详细部署步骤
- VPS 配置
- systemd 服务
- 故障排查

---

## 🔄 数据流程

### 频道收集流程

```
用户转发消息 → 私有频道
           ↓
    Bot 监听频道
           ↓
  extractor.py 提取链接
           ↓
   database.py 存入数据库
           ↓
    状态: pending
```

### 爬虫工作流程

```
crawler.py 读取 pending 频道
           ↓
    自动加入频道
           ↓
    监听新消息
           ↓
  转发到存储频道
           ↓
   建立搜索索引
           ↓
    状态: active
```

### 搜索流程

```
用户输入关键词
      ↓
search.py 解析查询
      ↓
database.py 查询数据库
      ↓
reports.py 格式化结果
      ↓
bot.py 返回用户
```

---

## 🧩 模块依赖关系

```
main.py
  ├─→ config.py
  ├─→ database.py
  ├─→ bot.py
  │    ├─→ config.py
  │    ├─→ database.py
  │    ├─→ extractor.py
  │    ├─→ reports.py
  │    └─→ search.py
  └─→ crawler.py
       ├─→ config.py
       └─→ database.py
```

---

## 🔐 安全考虑

### 敏感信息保护

1. `.env` 文件权限
2. `.gitignore` 忽略规则
3. Token 不硬编码

### UserBot 风险控制

1. 使用专用小号
2. 限制操作频率
3. 错误处理和重试

### 数据安全

1. 定期备份
2. 数据加密（可选）
3. 访问控制（管理员白名单）

---

## 📊 性能优化

### 数据库

- 建立索引（username、content）
- 定期 VACUUM
- 异步操作（aiosqlite）

### Bot 响应

- 按钮式交互
- 结果分页
- 缓存（未实现）

### 爬虫效率

- 批量操作
- 异步并发
- 限流保护

---

## 🚀 未来扩展

### 计划功能

- [ ] 全文搜索优化（jieba 分词）
- [ ] 搜索历史记录
- [ ] 热门关键词统计
- [ ] 频道推荐算法
- [ ] 数据导出（CSV/JSON）
- [ ] Web 管理界面
- [ ] 多语言支持
- [ ] 用户订阅功能
- [ ] 定时推送

### 技术升级

- [ ] Redis 缓存
- [ ] Elasticsearch 全文搜索
- [ ] PostgreSQL 替代 SQLite
- [ ] Docker 容器化
- [ ] 监控和告警系统

---

## 📞 技术支持

如有问题或建议，欢迎通过以下方式联系：

- 📧 提交 Issue
- 💬 Telegram: @jisousearchhelp_bot
- 📖 查看文档: README.md, USAGE.md, DEPLOYMENT.md

---

**项目结构说明完毕 🎉**

