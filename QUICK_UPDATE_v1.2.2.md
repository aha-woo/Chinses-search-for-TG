# 🚀 快速更新 v1.2.2 - 可配置延迟

## 📅 更新日期
2025-11-02

## ✨ 主要改进

### 🎯 可配置的延迟时间

**之前**：延迟固定为 1.5 秒，无法调整

**现在**：可以通过配置文件自定义延迟时间 ✅

---

## 🔧 新增配置

在你的 `.env` 文件中添加（如果没有就创建）：

```env
# 基础延迟（秒）- 默认 3.0 秒
CHANNEL_VERIFY_DELAY=5.0

# 随机延迟范围（秒）- 默认 1.0 秒
CHANNEL_VERIFY_RANDOM_DELAY=2.0
```

### 实际效果

以上配置：
- **实际延迟**：5.0 ~ 7.0 秒（随机）
- **50 个频道**：约 5-6 分钟
- **100 个频道**：约 10-12 分钟
- **触发速率限制风险**：几乎为 0 🛡️

---

## ⚡ 快速部署

### 1. 更新代码
```bash
cd ~/ChineseSearch
git pull origin main
```

### 2. 配置延迟（可选）

如果你说"不着急"，推荐设置：

```bash
# 编辑 .env 文件
nano .env
```

添加或修改：
```env
CHANNEL_VERIFY_DELAY=5.0
CHANNEL_VERIFY_RANDOM_DELAY=2.0
```

保存退出（Ctrl+X, Y, Enter）

### 3. 重启 Bot
```bash
pm2 restart telegram-search-bot
```

### 4. 验证
```bash
# 查看日志
pm2 logs telegram-search-bot --lines 20
```

转发一些链接到收集频道，观察日志输出。

---

## 📊 推荐配置

### 你说"不着急" → 推荐这个 ✅

```env
# 安全模式 - 100% 避免速率限制
CHANNEL_VERIFY_DELAY=5.0
CHANNEL_VERIFY_RANDOM_DELAY=2.0
```

**优势**：
- ✅ 不会触发速率限制
- ✅ 处理更稳定
- ✅ 数据质量更高
- ⏱️ 稍微慢一点（但你说不着急）

**速度**：
- 10 个频道 ≈ 1 分钟
- 50 个频道 ≈ 5 分钟
- 100 个频道 ≈ 10 分钟

---

## 🎯 默认值说明

如果你**不设置**这些参数，Bot 会使用默认值：

```env
CHANNEL_VERIFY_DELAY=3.0        # 默认 3 秒
CHANNEL_VERIFY_RANDOM_DELAY=1.0  # 默认 1 秒
```

**默认配置**：
- 适合日常使用
- 平衡速度和稳定性
- 较少触发速率限制

---

## 🔍 日志示例

### 启用 DEBUG 日志查看详细信息

编辑 `.env`：
```env
LOG_LEVEL=DEBUG
```

重启后，你会看到：
```
⏱️ 等待 5.7 秒后验证 @tech_news
📋 获取频道信息: 科技资讯 (@tech_news)
✅ 新频道: 科技资讯 - 科技数码

⏱️ 等待 6.2 秒后验证 @movie_share
📋 获取频道信息: 电影分享 (@movie_share)
✅ 新频道: 电影分享 - 影视资源

📺 消息 75 处理完成: ✅ 新增 2 个 ⏭️ 跳过 3 个
```

---

## 📈 对比表

| 配置 | 平均延迟 | 50个频道 | 速率限制风险 |
|-----|---------|---------|------------|
| 快速 (2.0s+0.5s) | 2.25s | ~2分钟 | 中 ⚠️ |
| 默认 (3.0s+1.0s) | 3.5s | ~3分钟 | 低 ✅ |
| **安全 (5.0s+2.0s)** | **6.0s** | **~5分钟** | **极低 🛡️** |
| 超安全 (10.0s+3.0s) | 11.5s | ~10分钟 | 几乎为0 |

**结论**：既然不着急，用"安全"配置最合适！

---

## 💡 使用建议

### 1. 初次使用
用默认配置（3 秒），观察几天，如果没问题就保持。

### 2. 大批量提取
如果需要一次提取 100+ 个频道：
```env
CHANNEL_VERIFY_DELAY=5.0   # 或更高
```

### 3. 夜间运行
如果可以夜间处理，设置更长延迟：
```env
CHANNEL_VERIFY_DELAY=8.0
CHANNEL_VERIFY_RANDOM_DELAY=3.0
```

晚上开始处理，早上查看结果。

### 4. 出现速率限制错误
如果看到 "Flood control exceeded"，立即增加延迟：
```env
CHANNEL_VERIFY_DELAY=8.0
```

---

## ⚠️ 注意事项

### 1. 修改配置后必须重启
```bash
pm2 restart telegram-search-bot
```

### 2. 查看当前配置
如果不确定是否生效，可以查看日志（需要 LOG_LEVEL=DEBUG）：
```bash
pm2 logs telegram-search-bot | grep "⏱️"
```

### 3. 不要设置太小
不建议设置 < 2.0 秒，容易触发限制。

---

## 📚 详细文档

想了解更多？查看：
- `DELAY_CONFIG_GUIDE.md` - 完整的延迟配置指南
- `env.example` - 所有配置参数示例
- `BUGFIX_v1.2.1.md` - 智能验证功能说明

---

## 🎉 总结

**核心改进**：
- ✅ 延迟时间可配置（之前固定）
- ✅ 添加随机延迟（更自然）
- ✅ 默认延迟从 1.5 秒增加到 3.0 秒
- ✅ 推荐"不着急"场景使用 5.0 秒

**推荐配置**（不着急）：
```env
CHANNEL_VERIFY_DELAY=5.0
CHANNEL_VERIFY_RANDOM_DELAY=2.0
```

**部署步骤**：
```bash
cd ~/ChineseSearch
git pull
# 编辑 .env 添加上面的配置
pm2 restart telegram-search-bot
```

完成！🎉

