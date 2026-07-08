---
name: algs-report-generator
description: 输入ApexLegendsStatus比赛URL，一键生成选手雷达图HTML画廊+手机友好PDF，并发送飞书通知。支持Overview自动监控，每天中午12点自动检查新比赛。自动爬取Liquipedia战队Logo和选手照片。
---

# ALGS 数据报告一键生成

## 方式 A：手动指定 URL

```bash
cd scripts
python generate_report.py "https://apexlegendsstatus.com/algs/Y6-Split1/ALGS-Playoffs/Global/Day1/CvD"
```

| 参数 | 说明 |
|------|------|
| `--skip-fetch` | 跳过抓取，使用已有 CSV |
| `--skip-pdf` | 跳过 PDF 生成 |
| `--skip-feishu` | 跳过飞书发送 |

## 方式 B：自动监控 Overview（推荐）

每天中午 12:00 自动检查 Overview 页面，发现新完成的比赛自动生成报告。

```bash
# 单次手动检查
cd scripts
python monitor_overview.py

# 持续监控（每30分钟）
python monitor_overview.py --watch
```

**已设置 Windows 定时任务：** `ALGS_Monitor` — 每天 12:00 触发。  
状态文件：`data/processed_matches.json`（记录已处理的比赛，避免重复）

```bash
# 查看定时任务
schtasks.exe //query //tn ALGS_Monitor

# 删除定时任务
schtasks.exe //delete //tn ALGS_Monitor //f
```

## 输出文件（均在 `data/` 下）

| 文件 | 说明 |
|------|------|
| `algs_players_data.csv` | 选手数据 CSV |
| `radar_charts/*.png` | 六边形雷达图 |
| `radar_gallery.html` | 交互式画廊（搜索筛选 + 弹窗详情含选手照片+战队Logo） |
| `algs_report.pdf` | 手机友好 PDF（封面 + 数据表 + 含选手照片+战队Logo的选手卡片） |
| `radar_collage.jpg` | 雷达图拼图 |
| `picture-ab/` | 战队Logo + 选手照片目录 |
| `processed_matches.json` | 监控状态（已处理的比赛记录） |

## 选手照片 & 战队Logo

### 画廊弹窗
点击雷达图卡片后，弹窗详情会显示该选手的真实照片（圆形头像）和所属战队Logo，无照片则显示占位符。

### PDF 报告
每个选手卡片中嵌入圆形选手照片和战队Logo（右上角），无照片则不做额外处理。

### 战队Logo & 选手照片爬取

从 Liquipedia Group Stage 页面一键爬取所有战队Logo和active选手照片：

```bash
cd scripts
python team_utils.py  # 测试映射功能

# 或直接调用爬取函数
python -c "from team_utils import crawl_team_logos_and_photos; crawl_team_logos_and_photos()"
```

图片保存至 `data/picture-ab/`：
- 战队Logo: `{缩写}.png`（如 `FLCN.png`）
- 选手照片: `{缩写}_{选手ID}.jpg/png`（如 `FLCN_ImperialHal.jpg`）

### 队名容错映射
`team_utils.py` 内置了多种队名变体的容错映射，支持：
- 精确匹配：`Team Falcons` → `FLCN`
- 大小写变体：`team falcons` → `FLCN`
- 缩写变体：`S8UL` → `S8UL`
- CSV中常见变体：`AURORA` → `AUR`

## 飞书通知

生成完毕后自动上传 HTML 画廊 + PDF 报告到飞书群并发送文字通知。

## 依赖

```
pip install "scrapling[all]>=0.4.10" beautifulsoup4 matplotlib pillow requests fpdf2
```

## 注意事项

- 需要先运行 `scrapling install --force` 安装浏览器依赖
- 飞书 Webhook URL 通过环境变量 `FEISHU_WEBHOOK_URL` 配置
- 监控脚本的 Overview URL 在 `scripts/monitor_overview.py` 中配置
- 选手照片需预先爬取到 `data/picture-ab/`，系统会自动查找并嵌入
