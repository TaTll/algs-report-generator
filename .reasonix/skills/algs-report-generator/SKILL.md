---
name: algs-report-generator
description: 自然语言驱动 ALGS 赛事数据报告生成——说句话即可完成数据抓取、雷达图、画廊、MD报告、飞书推送、剪映工程、网站更新全流程。
---

# ALGS 数据报告生成器

## 使用方式

直接用自然语言与 AI Agent 交互，无需手动执行脚本：

```
"更新 Survivor Stage 数据"
"把 B vs D 组素材导入剪映"
"网站加 Overall 排名"
"补上 CD 组数据"
```

Agent 自主拆解 → 执行 → 验证 → 推送。

## 输出

| 产物 | 说明 |
|------|------|
| 雷达图 | 60 张六边形极坐标图 |
| HTML 画廊 | 交互式，搜索+弹窗+照片 |
| MD 报告 | Top 10 + 战队排名 |
| 飞书通知 | 战绩卡片 + 数据预览 |
| 剪映工程 | 三轨道 180 秒自动合成 |
| 数据网站 | GitHub Pages，7 场比赛 |

## 子脚本（Agent 自动调用）

```
scripts/
├── generate_report.py      ← 主流程
├── build_jy_video.py       ← 剪映工程
├── update_all.py           ← 一键全更新
└── team_utils.py           ← 战队映射 + 爬虫
```

## 依赖

```bash
pip install scrapling[all] beautifulsoup4 matplotlib pillow requests
scrapling install --force
```

## 安全

飞书 Webhook URL 保存在本地 `scripts/.feishu_config`，已 gitignore，不会上传。
