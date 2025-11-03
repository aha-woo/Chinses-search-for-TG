# PM2 进程管理指南

使用 PM2 管理 Telegram 中文搜索 Bot 进程。

## 目录

1. [安装 PM2](#安装-pm2)
2. [启动 Bot](#启动-bot)
3. [日常管理](#日常管理)
4. [监控和日志](#监控和日志)
5. [故障排查](#故障排查)

---

## 安装 PM2

### 1. 安装 Node.js 和 npm

```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# 验证安装
node --version
npm --version
```

### 2. 安装 PM2

```bash
sudo npm install -g pm2

# 验证安装
pm2 --version
```

### 3. 设置开机自启

```bash
# 生成启动脚本
pm2 startup

# 按提示执行返回的命令，例如：
# sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u root --hp /root
```

---

## 启动 Bot

### 方式 1：使用配置文件（推荐）

```bash
cd ~/ChineseSearch

# 创建日志目录
mkdir -p logs

# 使用配置文件启动
pm2 start ecosystem.config.js

# 保存进程列表
pm2 save
```

### 方式 2：命令行启动

```bash
cd ~/ChineseSearch

pm2 start main.py \
  --name telegram-search-bot \
  --interpreter ./venv/bin/python \
  --log ./logs/combined.log \
  --time
  
# 保存
pm2 save
```

---

## 日常管理

### 查看进程状态

```bash
# 查看所有进程
pm2 list

# 或
pm2 status
```

**输出示例：**
```
┌─────┬──────────────────────────┬─────────┬─────────┬─────────┬──────────┐
│ id  │ name                     │ mode    │ ↺      │ status  │ cpu      │
├─────┼──────────────────────────┼─────────┼─────────┼─────────┼──────────┤
│ 0   │ telegram-search-bot      │ fork    │ 0       │ online  │ 0%       │
└─────┴──────────────────────────┴─────────┴─────────┴─────────┴──────────┘
```

### 重启 Bot

```bash
# 重启
pm2 restart telegram-search-bot

# 或使用 ID
pm2 restart 0
```

### 停止 Bot

```bash
# 停止
pm2 stop telegram-search-bot

# 停止所有
pm2 stop all
```

### 删除进程

```bash
# 删除进程（会从列表中移除）
pm2 delete telegram-search-bot

# 删除所有
pm2 delete all
```

### 重新加载（零停机）

```bash
pm2 reload telegram-search-bot
```

---

## 监控和日志

### 实时监控

```bash
# 实时监控面板
pm2 monit
```

按 `q` 或 `Ctrl+C` 退出。

### 查看日志

```bash
# 实时日志（所有进程）
pm2 logs

# 只看指定进程
pm2 logs telegram-search-bot

# 查看错误日志
pm2 logs telegram-search-bot --err

# 查看输出日志
pm2 logs telegram-search-bot --out

# 查看最近 100 行
pm2 logs telegram-search-bot --lines 100

# 清空日志
pm2 flush
```

### 查看详细信息

```bash
# 查看进程详情
pm2 describe telegram-search-bot

# 或
pm2 show telegram-search-bot
```

### 日志文件位置

根据 `ecosystem.config.js` 配置：

```
~/ChineseSearch/logs/
├── err.log         # 错误日志
├── out.log         # 输出日志
└── combined.log    # 合并日志
```

---

## 更新 Bot

### 更新代码后重启

```bash
cd ~/ChineseSearch

# 拉取最新代码（如果使用 Git）
git pull

# 或上传新文件
# scp bot.py root@server:~/ChineseSearch/

# 重启 Bot
pm2 restart telegram-search-bot
```

### 更新依赖

```bash
cd ~/ChineseSearch
source venv/bin/activate

# 更新依赖
pip install -r requirements.txt

# 重启
pm2 restart telegram-search-bot
```

---

## 高级功能

### 自动重启（内存限制）

如果 Bot 内存超过 500MB 自动重启（已在 `ecosystem.config.js` 配置）：

```javascript
max_memory_restart: '500M'
```

### 监控 CPU 和内存

```bash
# 实时监控
pm2 monit

# 或查看资源使用
pm2 status
```

### 查看重启次数

```bash
pm2 list
```

查看 `↺` 列，显示重启次数。

### 定时重启（可选）

```bash
# 每天凌晨 3 点重启
pm2 restart telegram-search-bot --cron "0 3 * * *"
```

---

## 故障排查

### Bot 无法启动

**检查步骤：**

1. **查看日志**
   ```bash
   pm2 logs telegram-search-bot --lines 50
   ```

2. **检查进程状态**
   ```bash
   pm2 list
   ```
   
   状态应该是 `online`，如果是 `errored` 说明启动失败。

3. **手动测试**
   ```bash
   cd ~/ChineseSearch
   source venv/bin/activate
   python main.py
   ```
   
   查看错误信息。

4. **检查配置**
   ```bash
   cat .env
   ```

5. **检查 Python 路径**
   ```bash
   which python
   # 应该显示：/root/ChineseSearch/venv/bin/python
   ```

### Bot 频繁重启

**可能原因：**

1. **内存不足**
   ```bash
   free -h
   ```

2. **代码错误**
   ```bash
   pm2 logs telegram-search-bot --err --lines 100
   ```

3. **网络问题**
   检查是否能访问 Telegram API

### 日志文件过大

```bash
# 清空日志
pm2 flush

# 或手动删除
rm ~/ChineseSearch/logs/*.log
```

**自动日志轮转（推荐）：**

```bash
# 安装 pm2-logrotate
pm2 install pm2-logrotate

# 配置（每天轮转，保留 7 天）
pm2 set pm2-logrotate:max_size 50M
pm2 set pm2-logrotate:retain 7
pm2 set pm2-logrotate:compress true
```

### PM2 进程丢失

如果重启服务器后 PM2 进程不见了：

```bash
# 恢复进程
pm2 resurrect

# 如果不行，重新启动
cd ~/ChineseSearch
pm2 start ecosystem.config.js
pm2 save
```

---

## 常用命令速查

| 命令 | 说明 |
|------|------|
| `pm2 start ecosystem.config.js` | 启动 Bot |
| `pm2 list` | 查看进程列表 |
| `pm2 restart telegram-search-bot` | 重启 Bot |
| `pm2 stop telegram-search-bot` | 停止 Bot |
| `pm2 logs telegram-search-bot` | 查看日志 |
| `pm2 monit` | 实时监控 |
| `pm2 save` | 保存进程列表 |
| `pm2 resurrect` | 恢复进程 |
| `pm2 delete telegram-search-bot` | 删除进程 |
| `pm2 flush` | 清空日志 |

---

## 性能优化

### 1. 调整日志级别

编辑 `.env`：

```env
LOG_LEVEL=WARNING  # 只记录警告和错误
```

### 2. 限制日志大小

使用 `pm2-logrotate`（见上文）

### 3. 监控资源使用

```bash
# 查看详细资源使用
pm2 describe telegram-search-bot
```

### 4. 定期重启

```bash
# 每周一凌晨 3 点重启
pm2 restart telegram-search-bot --cron "0 3 * * 1"
```

---

## 备份和恢复

### 备份 PM2 配置

```bash
# 保存当前进程列表
pm2 save

# 配置文件位置
~/.pm2/dump.pm2
```

### 恢复 PM2 进程

```bash
# 恢复所有进程
pm2 resurrect
```

---

## 与 systemd 对比

| 功能 | PM2 | systemd |
|------|-----|---------|
| 易用性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 实时监控 | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| 日志管理 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 跨平台 | ⭐⭐⭐⭐ | ⭐⭐ |
| 系统集成 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**推荐：**
- 开发/测试环境：PM2（更方便）
- 生产环境：两者都可以

---

## 附加功能

### Web 界面监控（可选）

```bash
# 安装 PM2 Web 界面
pm2 install pm2-web

# 访问 http://your_server_ip:9615
```

### 远程监控（可选）

```bash
# 注册 PM2 Plus（免费）
pm2 register

# 或使用 Keymetrics
pm2 link <secret_key> <public_key>
```

---

## 参考资源

- PM2 官方文档: https://pm2.keymetrics.io/
- PM2 GitHub: https://github.com/Unitech/pm2
- PM2 命令参考: https://pm2.keymetrics.io/docs/usage/quick-start/

---

## 技术支持

遇到问题？

1. 查看 [DEPLOYMENT.md](DEPLOYMENT.md)
2. 查看 [README.md](README.md)
3. 检查 PM2 日志
4. 联系管理员

---

**使用 PM2 轻松管理你的 Bot！🚀**

