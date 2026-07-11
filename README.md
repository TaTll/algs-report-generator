# ALGS 赛事数据智能报告系统

> 🤖 AI Agent 驱动 | 说句话就能更新比赛数据、生成报告、合成视频

## 使用方式

不需要手动执行脚本，直接用自然语言与 AI Agent 交互：

```
"更新 B vs D 组比赛数据"
"抓 Survivor Stage，素材导入剪映"
"更新网站，加 Overall 排名"
"CD 组数据补上"
```

Agent 自主完成：抓取 → 清洗 → 雷达图 → MD 报告 → 网站更新 → 飞书推送 → Git 部署。

## 功能

- 🕷️ **数据抓取** — Scrapling 自动抓取 ApexLegendsStatus
- 📊 **雷达图** — 六边形极坐标，含全选手平均值对比
- 🖼️ **画廊** — 交互式 HTML，搜索/筛选/弹窗详情/选手照片/Logo
- 📝 **MD 报告** — Top 10 + 战队排名，飞书 lark_md 推送
- 📮 **飞书通知** — 战绩卡片 + 数据预览自动推送
- 🎬 **剪映工程** — 三轨道（雷达图 + 照片 + Logo）自动合成
- 🌐 **数据网站** — GitHub Pages，7 场比赛 + 40 队积分 + 121 选手汇总
- 🏷️ **战队映射** — 三级容错（`AURORA` → `AUR`），支持多数据源
- 📷 **照片爬取** — Liquipedia 一键下载 40 队 Logo + 120+ 选手照片

## 网站

https://TaTll.github.io/algs-report-generator/

## 技术栈

Python · Scrapling · Matplotlib · BeautifulSoup4 · Pillow · 飞书 Webhook · 剪映 API · GitHub Pages

## AI 协作模式

本项目全部代码由 AI Agent（Claude / Reasonix）在 Agent + Human-in-the-loop 模式下编写。用户通过自然语言下达目标，Agent 自主拆解任务、生成代码、调试部署、修复异常。人类仅在关键决策点确认。
