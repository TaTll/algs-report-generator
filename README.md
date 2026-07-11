# ALGS 赛事数据智能报告系统

> 🤖 AI Agent 驱动 | 说句话就能更新比赛数据、生成报告、合成视频

## 项目流程

```
用户: "更新 Survivor Stage 数据"
  │
  ▼
┌─────────────────────────────────────────────┐
│  AI Agent 自主执行                            │
│                                             │
│  抓取 → CSV → 雷达图 → MD报告 → 飞书推送     │
│                    ↓                        │
│               网站更新 → GitHub Pages 部署    │
│                    ↓                        │
│               剪映工程 → 选手照片 + Logo      │
└─────────────────────────────────────────────┘
```

## 产物展示

### 数据网站
https://TaTll.github.io/algs-report-generator/

<img src="https://TaTll.github.io/algs-report-generator/thumbs/ac_ELTE_KIND4.jpg" width="160"> <img src="https://TaTll.github.io/algs-report-generator/thumbs/ac_ELTE_IHenchman.jpg" width="160"> <img src="https://TaTll.github.io/algs-report-generator/thumbs/ac_AG_YanYa.jpg" width="160">

### 剪映视频工程

三轨道自动合成（雷达图 + 选手照片 + 战队 Logo）：

| Radar 轨道 | Photo 轨道 | Logo 轨道 |
|:--:|:--:|:--:|
| 六边形雷达图 + 字幕 | 选手照片 | 战队 Logo |
| 每张 3 秒，同选手同时出现 | | |

### 飞书推送

自动发送战绩卡片 + MD 数据预览到群聊。

## 功能

- 🕷️ 数据抓取 · 📊 雷达图 · 🖼️ 画廊 · 📝 MD 报告
- 📮 飞书通知 · 🎬 剪映工程 · 🌐 数据网站
- 🏷️ 战队容错映射 · 📷 照片爬取

## 技术栈

Python · Scrapling · Matplotlib · BeautifulSoup4 · Pillow · 飞书 Webhook · 剪映 API · GitHub Pages

## AI 协作模式

全部代码由 AI Agent（Claude / Reasonix）在 Agent + Human-in-the-loop 模式下编写。用户自然语言下达目标，Agent 自主拆解→生成→调试→部署。
