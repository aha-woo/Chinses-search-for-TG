# 功能说明

本文档详细说明项目的各项功能特性。

## 📺 频道列表功能

### 功能特点
- 简洁显示频道信息
- 分类筛选频道
- 翻页浏览大量频道
- 实时刷新数据
- 直达链接

### 使用方法
```
/list
```
或通过 `/start` 菜单中的"📺 频道列表"按钮

详见：[FEATURE_CHANNEL_LIST.md](FEATURE_CHANNEL_LIST.md)

---

## 📋 频道元信息存储功能

### 设计理念
频道元信息也是搜索数据的一部分，应该统一存储到 SearchDataStore 频道。

### 实现方案
- 使用 `#频道元信息` 标签区分频道元信息和消息内容
- 格式化频道卡片显示
- 包含名称、ID、分类、成员数等完整信息

详见：[FEATURE_CHANNEL_METADATA_v1.3.0.md](FEATURE_CHANNEL_METADATA_v1.3.0.md)

