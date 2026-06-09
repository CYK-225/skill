---
name: douyin-analytics
description: 抖音创作者视频数据抓取与分析。触发词：抖音数据、douyin、抓取抖音、抖音分析、抖音博主数据、抖音视频列表、抖音主页数据。当用户提供抖音用户主页 URL 或想获取某抖音博主视频数据时自动激活。
---

# 抖音数据抓取技能

根据抖音用户主页 URL 和 Cookie，抓取该用户发布的视频列表数据，包含标题、发布日期、点赞/评论/分享/播放数据，以表格形式汇报。

## 工作流程

**严格按照以下顺序执行，每步确认后再继续：**

### 第一步：收集必要信息

依次询问用户以下信息：

1. **目标抖音用户主页 URL**
   - 格式示例：`https://www.douyin.com/user/MS4wLjABAAAA...`
   - 从 URL 中提取 `sec_user_id` 参数

2. **抖音登录 Cookie**
   - 引导用户：打开浏览器开发者工具 (F12) → Network 标签 → 刷新页面 → 找到任意 douyin.com 请求 → 复制 Request Headers 中的 Cookie 值
   - Cookie 必须包含 `sessionid` 字段，否则无法获取数据

3. **抓取时间范围**
   - 询问：抓取最近多少天的视频？
   - 默认值：7 天
   - 建议范围：1-30 天

### 第二步：准备环境

```bash
# 将 Cookie 写入临时文件
echo "<用户提供的Cookie>" > /tmp/dy_cookie.txt

# 确保 requests 库可用
pip install requests -q
```

### 第三步：执行数据抓取

运行 `scripts/fetch_videos.py` 脚本：

```bash
python ~/.openclaw/workspace/skills/douyin-analytics/scripts/fetch_videos.py \
  --sec_user_id "<从URL提取的sec_user_id>" \
  --cookie_file /tmp/dy_cookie.txt \
  --days <用户指定的天数>
```

### 第四步：汇报结果

以表格形式展示抓取结果：

| 序号 | 标题 | 发布日期 | 点赞 | 评论 | 分享 | 播放 |
|------|------|----------|------|------|------|------|
| 1 | ... | ... | ... | ... | ... | ... |

**数据摘要：**
- 视频总数：X 条
- 平均播放量：X
- 最高播放视频：[标题] (X 次播放)

## 错误处理

| 错误码 | 含义 | 解决方案 |
|--------|------|----------|
| status_code=2 | Cookie 无效或过期 | 提示用户重新从浏览器 Network 面板获取 Cookie，确保包含完整值 |
| status_code=8 | 需要登录 | 提示用户重新登录抖音网页版，然后获取新 Cookie |
| 网络错误 | 连接失败 | 检查网络连接，或建议用户使用 VPN |

## 注意事项

- Cookie 包含敏感信息，仅在本次会话使用，不会存储
- 抖音 API 可能有频率限制，大量抓取时建议间隔请求
- 视频数据可能不完整，部分视频可能无播放量数据