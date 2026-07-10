---
name: algs-report-generator
description: 输入ApexLegendsStatus比赛URL，一键生成选手雷达图HTML画廊+MD数据报告+飞书通知+剪映工程+数据网站。支持Overview自动监控。自动爬取Liquipedia战队Logo和选手照片。
---

# ALGS 数据报告生成器

## 🚀 一键更新

```bash
cd scripts

# 抓取新比赛 + 建网站 + 推GitHub（全自动）
python update_all.py --group ad --url "https://apexlegendsstatus.com/algs/Y6-Split1/ALGS-Playoffs/Global/Day3/AvD"

# 已有CSV，只重建网站+推送
python update_all.py --group ad --skip-fetch

# 只重建网站+推送（不抓数据）
python update_all.py --website-only
```

## ⚡ 子功能

```bash
# 生成剪映视频工程（三轨道：雷达图+照片+Logo）
python build_jy_video.py --group ad

# 爬取战队Logo+选手照片
python -c "from team_utils import crawl_team_logos_and_photos; crawl_team_logos_and_photos()"

# 自动监控 Overview
python monitor_overview.py
```

## 📁 输出

```
data/{group}/
├── algs_players_data.csv      ← 选手数据
├── radar_charts/              ← 雷达图
├── radar_gallery.html         ← 交互式画廊
└── preview.md                 ← MD 报告

public/  →  GitHub Pages       ← 数据网站
```

## 🖥️ 数据网站

https://TaTll.github.io/algs-report-generator/

- Tab 切换各组别
- Team Data / Player Data 视图
- List / Radar Charts 子视图
- 点击弹窗：雷达图 + 选手照片 + 详细数据

## 📮 飞书通知

Webhook URL 保存至 `scripts/.feishu_config`，自动发送摘要卡片+MD数据预览。

## 🔧 依赖

```bash
pip install "scrapling[all]>=0.4.10" beautifulsoup4 matplotlib pillow requests
scrapling install --force
```
