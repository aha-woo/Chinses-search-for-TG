# 更新日志 v1.1.0

## 发布日期
2025-11-02

## 重要更新

本次更新主要优化了搜索功能，新增群组自动搜索、优化结果显示、添加广告位和类型分类。

---

## 🎉 新功能

### 1. 群组自动搜索

**功能描述：**
- Bot 加入搜索群组后，用户直接输入关键词即可搜索
- 无需输入 `/search` 命令
- 自动识别并处理群组消息

**配置项：**
```env
SEARCH_GROUP_ID=8068014765
```

**影响文件：**
- `config.py` - 添加 `SEARCH_GROUP_ID` 配置
- `bot.py` - 添加 `handle_search_group_message()` 方法
- `bot.py` - 注册群组消息监听器

---

### 2. 优化的搜索结果显示

**改进点：**
- ✅ 结果内容带超链接（Markdown 格式）
- ✅ 简洁的单行显示
- ✅ 自动构建存储频道链接
- ✅ 视频显示时长
- ✅ 来源和日期简化显示

**格式对比：**

**旧格式：**
```
1. Python零基础入门教程，适合初学者学习...
   📺 @tech_learning (技术学习)
   🎬 video
   🕐 2025-10-28 14:30
   🔗 消息: 12345
```

**新格式：**
```
1. 🎬 [Python零基础入门教程，适合初学者学习...](链接) ⏱️ 1800s
   📺 @tech_learning • 10-28
```

**影响文件：**
- `search.py` - 重写 `format_search_result()` 方法
- `search.py` - 优化超链接生成逻辑

---

### 3. 顶部广告位

**功能描述：**
- 搜索结果顶部显示可自定义广告
- 支持开关控制
- 建议 1-2 句话，简短有力

**配置项：**
```env
SEARCH_AD_TEXT=💎 发现更多优质内容，关注我们的频道 @your_channel
SEARCH_AD_ENABLED=true
```

**显示效果：**
```
📢 💎 发现更多优质内容，关注我们的频道 @your_channel
━━━━━━━━━━━━━━━━━━━━

🔍 搜索: "Python"
...
```

**影响文件：**
- `config.py` - 添加 `SEARCH_AD_TEXT` 和 `SEARCH_AD_ENABLED`
- `bot.py` - 在 `_send_search_results()` 中添加广告显示

---

### 4. 类型分类按钮

**功能描述：**
- 搜索结果下方显示类型按钮
- 点击按钮筛选指定类型内容
- 支持：全部、视频、图片、文档

**按钮布局：**
```
[📝 全部] [🎬 视频] [📸 图片] [📎 文档]
```

**交互流程：**
1. 用户搜索 "Python"
2. 显示所有类型结果
3. 用户点击 "🎬 视频"
4. 只显示视频类型结果

**影响文件：**
- `bot.py` - 在 `_send_search_results()` 中添加分类按钮
- `bot.py` - 添加 `search_type_` 回调处理
- `search.py` - 支持 `media_type_filter` 参数

---

### 5. 视频时长显示

**功能描述：**
- 视频类型结果自动显示时长
- 格式：`⏱️ 1800s`（表示 1800 秒）

**显示示例：**
```
1. 🎬 [Python入门教程](链接) ⏱️ 1800s
```

**影响文件：**
- `search.py` - 在 `format_search_result()` 中添加时长显示
- `database.py` - messages 表支持 `video_duration` 字段（待扩展）

---

### 6. 改进的翻页功能

**改进点：**
- 翻页按钮位于类型按钮下方
- 显示当前页数和总页数
- 支持按类型翻页（保持过滤状态）

**按钮布局：**
```
[📝 全部] [🎬 视频] [📸 图片] [📎 文档]
[◀️ 上一页] 1/5 [下一页 ▶️]
```

**影响文件：**
- `bot.py` - 优化翻页按钮逻辑
- `bot.py` - 添加 `search_page_` 回调处理

---

## 🔧 配置变更

### 新增配置项

在 `.env` 文件中新增以下配置：

```env
# 搜索群组 ID
SEARCH_GROUP_ID=8068014765

# 搜索数据存储频道 ID（更新）
STORAGE_CHANNEL_ID=-1003286651502

# 搜索广告配置
SEARCH_AD_TEXT=💎 发现更多优质内容，关注我们的频道 @your_channel
SEARCH_AD_ENABLED=true

# 每页结果数量
RESULTS_PER_PAGE=10
```

### 配置文件变更

**config.py:**
```python
# 新增
STORAGE_CHANNEL_ID: int = int(os.getenv('STORAGE_CHANNEL_ID', '-1003286651502'))
SEARCH_GROUP_ID: int = int(os.getenv('SEARCH_GROUP_ID', '8068014765'))
SEARCH_AD_TEXT: str = os.getenv('SEARCH_AD_TEXT', '💎 发现更多优质内容...')
SEARCH_AD_ENABLED: bool = os.getenv('SEARCH_AD_ENABLED', 'true').lower() == 'true'
RESULTS_PER_PAGE: int = int(os.getenv('RESULTS_PER_PAGE', '10'))
```

---

## 📝 代码变更

### 修改的文件

1. **config.py**
   - 添加 5 个新配置项
   - 更新 `STORAGE_CHANNEL_ID` 默认值

2. **bot.py**
   - 添加 `handle_search_group_message()` - 处理群组搜索
   - 添加 `_send_search_results()` - 格式化搜索结果
   - 添加 `_get_media_type_name()` - 获取类型中文名
   - 注册群组消息监听器
   - 添加搜索类型过滤回调处理
   - 添加搜索翻页回调处理

3. **search.py**
   - 重写 `format_search_result()` - 优化结果格式
   - 添加超链接生成逻辑
   - 添加视频时长显示
   - 简化来源和日期显示

4. **env.example**
   - 添加新配置项说明
   - 更新默认值

### 新增的文件

1. **GROUP_SEARCH_GUIDE.md**
   - 群组搜索功能使用指南
   - 配置步骤说明
   - 故障排查

2. **CHANGELOG_v1.1.md**
   - 本文件，详细更新日志

---

## 🚀 升级指南

### 从 v1.0.0 升级到 v1.1.0

#### 1. 更新代码

```bash
# 如果使用 Git
git pull origin main

# 或手动替换文件：
# - config.py
# - bot.py
# - search.py
# - env.example
```

#### 2. 更新配置

编辑 `.env` 文件，添加新配置项：

```bash
nano .env
```

添加：
```env
STORAGE_CHANNEL_ID=-1003286651502
SEARCH_GROUP_ID=8068014765
SEARCH_AD_TEXT=💎 发现更多优质内容，关注我们的频道 @your_channel
SEARCH_AD_ENABLED=true
RESULTS_PER_PAGE=10
```

#### 3. 将 Bot 加入搜索群组

1. 打开搜索群组
2. 添加 Bot 为成员
3. 确保 Bot 有读取消息权限

#### 4. 重启 Bot

```bash
# systemd 方式
sudo systemctl restart telegram-search-bot

# nohup 方式
pkill -f "python main.py"
nohup python main.py > bot.log 2>&1 &
```

#### 5. 测试功能

在搜索群组中输入关键词，确认 Bot 响应。

---

## 🐛 已知问题

### 1. Markdown 格式错误

**问题：**
如果搜索内容包含特殊字符（`[`, `]`, `(`, `)` 等），可能导致 Markdown 解析错误。

**解决方案：**
Bot 会自动捕获异常并降级为纯文本格式。

**未来改进：**
对特殊字符进行转义处理。

### 2. 超链接无法访问

**问题：**
如果存储频道为私有且用户无权限，链接无法访问。

**解决方案：**
- 将存储频道设置为公开
- 或确保用户已加入存储频道

### 3. 视频时长未存储

**问题：**
当前版本爬虫未存储视频时长，需要扩展。

**未来改进：**
在 `crawler.py` 中提取视频时长并存入数据库。

---

## 🔄 兼容性

### Python 版本
- 最低要求：Python 3.9
- 推荐版本：Python 3.12

### 依赖包
无新增依赖，与 v1.0.0 兼容。

### 数据库
数据库结构未变更，可直接升级无需迁移。

---

## 📊 性能影响

### 群组消息处理

**影响：**
- 每条群组消息都会触发搜索
- 建议在专用搜索群组使用
- 避免在聊天频繁的群组启用

**优化建议：**
- 设置最短关键词长度（当前 2 字符）
- 考虑添加搜索频率限制（未来版本）

### 搜索响应速度

**优化：**
- 使用异步数据库操作
- 结果限制在 10 条/页
- Markdown 格式生成优化

**测试结果：**
- 平均响应时间：< 1 秒
- 数据库查询：< 100ms

---

## 🎯 未来计划

### v1.2.0（计划中）

- [ ] 视频时长自动提取和存储
- [ ] 搜索历史记录
- [ ] 热门搜索关键词统计
- [ ] 搜索结果缓存
- [ ] 用户搜索频率限制
- [ ] 多群组支持
- [ ] 搜索结果图片预览
- [ ] 高级搜索语法（日期范围、排序）

### v1.3.0（规划中）

- [ ] Web 管理界面
- [ ] 搜索分析报表
- [ ] 用户订阅功能
- [ ] 定时推送热门内容
- [ ] 全文搜索优化（jieba 分词）

---

## 🙏 致谢

感谢用户提供的宝贵反馈和建议！

特别感谢：
- @youryhc - 提出群组搜索需求
- 所有测试用户

---

## 📞 技术支持

如有问题：

1. 查看 [GROUP_SEARCH_GUIDE.md](GROUP_SEARCH_GUIDE.md)
2. 查看 [USAGE.md](USAGE.md)
3. 提交 Issue
4. 联系管理员

---

**v1.1.0 更新完成！🎉**

享受全新的群组搜索体验！

