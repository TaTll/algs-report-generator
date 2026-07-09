---
name: algs-report-generator
description: 输入ApexLegendsStatus比赛URL，一键生成选手雷达图HTML画廊+MD数据报告，并发送飞书通知。支持Overview自动监控。自动爬取Liquipedia战队Logo和选手照片。
---

# ALGS 数据报告一键生成

## 方式 A：手动指定 URL

```bash
cd scripts
python generate_report.py "https://apexlegendsstatus.com/algs/Y6-Split1/ALGS-Playoffs/Global/Day2/BvD" --group bd
```

| 参数 | 说明 |
|------|------|
| `--group bd` | 输出到 `data/bd/` 子目录 |
| `--skip-fetch` | 跳过抓取，使用已有 CSV |
| `--skip-md` | 跳过 MD 报告生成 |
| `--skip-feishu` | 跳过飞书发送 |

## 方式 B：自动监控 Overview

```bash
cd scripts
python monitor_overview.py        # 单次检查
python monitor_overview.py --watch # 持续监控（每30分钟）
```

## 输出目录结构

```
data/
├── picture-ab/          ← 共享：战队Logo + 选手照片
├── ab/                  ← A vs B 组
│   ├── algs_players_data.csv
│   ├── radar_charts/
│   ├── radar_gallery.html
│   └── preview.md
├── cd/                  ← C vs D 组
└── bd/                  ← B vs D 组
```

## 输出文件

| 文件 | 说明 |
|------|------|
| `algs_players_data.csv` | 选手数据 CSV |
| `radar_charts/*.png` | 六边形雷达图（含选手+平均对比） |
| `radar_gallery.html` | 交互式画廊（搜索筛选 + 弹窗详情含选手照片+Logo） |
| `preview.md` | **MD 数据报告**（Top 10 + 战队排名，飞书友好格式） |
| `radar_collage.jpg` | 雷达图拼图 |

## 选手照片 & 战队Logo

- 画廊弹窗：点击雷达图 → 显示选手照片 + 数据详情
- 自动查找 `data/picture-ab/` 中的照片（格式：`{缩写}_{选手ID}.jpg`）

爬取照片：
```bash
cd scripts
python -c "from team_utils import crawl_team_logos_and_photos; crawl_team_logos_and_photos()"
```

## 飞书通知

生成完毕后自动发送：
1. **摘要卡片** — 比赛标题 + 选手数 + 文件路径
2. **MD 数据卡片** — Top 10 排行榜 + 战队排名全文

飞书 Webhook URL 保存至 `scripts/.feishu_config`

## 依赖

```bash
pip install "scrapling[all]>=0.4.10" beautifulsoup4 matplotlib pillow requests
```

- 需要 `scrapling install --force` 安装浏览器依赖
- 选手照片需预先爬取到 `data/picture-ab/`
- 不再需要 fpdf2（已取消 PDF 输出）

## 🎬 剪映工程生成

将雷达图 + 选手照片 + 战队Logo 导入剪映时间轴，自动创建三轨道视频工程：

```bash
cd scripts

# 生成 AC 组剪映工程
python build_jy_video.py --group ac

# 指定草稿名称和图片时长
python build_jy_video.py --group bd --name "ALGS_BD_Showcase" --duration 4s
```

| 参数 | 说明 |
|------|------|
| `--group ac` | 组别（对应 `data/{group}/` 目录） |
| `--name` | 草稿名称（默认 `ALGS_{GROUP}_Group`） |
| `--duration` | 每张图显示时长（默认 `3s`） |

### 时间轴结构

| 轨道 | 内容 |
|------|------|
| **Radar**（上层） | 六边形雷达图 + 选手名字幕 |
| **Photo**（中层） | 选手照片 |
| **Logo**（下层） | 战队Logo |

同一选手的三张图**同时出现**，时长统一，按战队排序依次播放。

### 前提条件

- 已安装 [jianying-editor](https://github.com/GuanYixuan/pyJianYingDraft) Skill
- 已生成对应组别的雷达图（运行过 `generate_report.py --group xx`）
- 已爬取选手照片到 `data/picture-ab/`
- 剪映运行时不要锁定草稿文件夹
