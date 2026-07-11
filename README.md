# ALGS 赛事数据智能报告系统

> 🤖 Agent + Human-in-the-loop 协作开发 | 输入比赛 URL → 全自动生成报告、视频、网站

## 功能

- 🕷️ **数据抓取** — Scrapling 自动抓取 ApexLegendsStatus 选手表格
- 📊 **雷达图** — 六边形极坐标雷达图，含全选手平均值对比
- 🖼️ **画廊** — 交互式 HTML，搜索/筛选/弹窗详情/选手照片/战队 Logo
- 📝 **MD 报告** — Top 10 击杀/伤害 + 战队排名，飞书 lark_md 兼容
- 📮 **飞书通知** — 自动推送战绩卡片 + MD 数据预览
- 🎬 **剪映工程** — 三轨道时间轴（雷达图 + 照片 + Logo），180 秒自动合成
- 🌐 **数据网站** — GitHub Pages 部署，6 场比赛 + 40 队积分 + 121 选手汇总
- 🏷️ **战队映射** — 三级容错匹配（`AURORA` → `AUR`）
- 📷 **照片爬取** — Liquipedia 一键下载 40 队 Logo + 120+ 选手照片

## 网站

https://TaTll.github.io/algs-report-generator/

| Tab | 内容 |
|------|------|
| Overall Standings | 40 队总积分排名（Finals/Survivor/Eliminated） |
| All Players | 121 名选手小组赛数据汇总 |
| Group Stage ▼ | 7 场比赛（6 组 + Survivor），List / Radar 双视图 |

## 快速开始

```bash
pip install scrapling[all] beautifulsoup4 matplotlib pillow requests
scrapling install --force

# 爬取照片（首次）
cd scripts
python -c "from team_utils import crawl_team_logos_and_photos; crawl_team_logos_and_photos()"

# 一键生成报告
python generate_report.py "URL" --group xx

# 一键更新网站
python update_all.py --group xx --url "URL"

# 生成剪映视频工程
python build_jy_video.py --group xx
```

## 飞书配置

将 Webhook URL 保存至 `scripts/.feishu_config`（已 gitignore，不会泄露）

## 项目结构

```
scripts/
├── generate_report.py      ← 主入口：抓取→CSV→雷达图→MD→飞书
├── generate_algs_report.py ← 雷达图生成
├── send_gallery.py         ← HTML 交互式画廊
├── send_feishu.py          ← 飞书推送
├── team_utils.py           ← 战队映射 + 照片爬虫
├── build_jy_video.py       ← 剪映工程生成
├── update_all.py           ← 一键更新（抓取+建站+推送）
└── monitor_overview.py     ← 自动监控

build_app.py                ← 网站构建器
docs/                       ← GitHub Pages
```

## AI 协作模式

本项目全部代码由 AI Agent（Claude / Reasonix）在 Human-in-the-loop 模式下编写。Agent 自主完成代码生成、调试、异常修复，人工仅负责目标定义与关键决策确认。
