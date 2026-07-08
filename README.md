# ALGS 数据报告生成器

> 输入 ApexLegendsStatus 比赛 URL，一键生成选手六边形雷达图、交互式 HTML 画廊、MD 数据报告，并自动发送飞书通知。

## 功能

- 🕷️ **数据抓取** — Scrapling 自动抓取 ApexLegendsStatus 选手数据
- 📊 **六边形雷达图** — 60 张个人雷达图，含全选手平均对比
- 🖼️ **交互式画廊** — HTML 页面，支持搜索筛选 + 弹窗详情 + 选手照片 + 战队 Logo
- 📝 **MD 数据报告** — Top 10 伤害榜 + 战队排名，飞书 lark_md 兼容格式
- 📮 **飞书通知** — 自动发送摘要卡片 + MD 数据预览
- 🤖 **自动监控** — 每天 12:00 检查 Overview，发现新比赛自动生成报告
- 🏷️ **战队映射** — 队名容错匹配，支持 CSV 中各种变体（如 `AURORA`→`AUR`）
- 📷 **照片爬取** — 一键从 Liquipedia 下载 40 支战队 Logo + 120+ 选手照片

## 输出示例

```
data/bd/
├── algs_players_data.csv    ← 60 名选手原始数据
├── radar_charts/            ← 60 张六边形雷达图 PNG
├── radar_gallery.html       ← 交互式画廊（搜索 + 弹窗 + 照片）
├── preview.md               ← MD 数据报告
└── radar_collage.jpg        ← 雷达图拼图
```

## 快速开始

### 安装依赖

```bash
pip install "scrapling[all]>=0.4.10" beautifulsoup4 matplotlib pillow requests
scrapling install --force
```

### 爬取战队 Logo 和选手照片（首次使用）

```bash
cd scripts
python -c "from team_utils import crawl_team_logos_and_photos; crawl_team_logos_and_photos()"
```

### 生成报告

```bash
cd scripts

# 从 URL 抓取数据并生成报告
python generate_report.py "https://apexlegendsstatus.com/algs/Y6-Split1/ALGS-Playoffs/Global/Day2/BvD" --group bd

# 使用已有 CSV 生成（跳过抓取）
python generate_report.py --skip-fetch --group bd
```

| 参数 | 说明 |
|------|------|
| `--group bd` | 输出到 `data/bd/` 子目录 |
| `--skip-fetch` | 跳过抓取，使用已有 CSV |
| `--skip-md` | 跳过 MD 报告生成 |
| `--skip-feishu` | 跳过飞书发送 |

### 配置飞书通知（可选）

1. 在飞书群中添加**自定义机器人**，获取 Webhook URL
2. 设置环境变量或保存到配置文件：

```bash
# 方式 A：环境变量
set FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx

# 方式 B：保存到文件（推荐）
echo "https://open.feishu.cn/open-apis/bot/v2/hook/xxx" > scripts/.feishu_config
```

### 自动监控

```bash
cd scripts
python monitor_overview.py        # 单次检查
python monitor_overview.py --watch # 每 30 分钟循环检查
```

## 目录结构

```
.
├── scripts/
│   ├── generate_report.py        ← 主入口：一键生成报告
│   ├── generate_algs_report.py   ← 雷达图生成
│   ├── send_gallery.py           ← HTML 交互式画廊
│   ├── send_feishu.py            ← 飞书排行榜推送
│   ├── team_utils.py             ← 战队映射 + 照片爬取
│   └── monitor_overview.py       ← Overview 自动监控
├── data/
│   ├── picture-ab/               ← 战队 Logo + 选手照片（共享）
│   ├── ab/                       ← A vs B 组
│   ├── cd/                       ← C vs D 组
│   └── bd/                       ← B vs D 组
└── .reasonix/skills/algs-report-generator/
    └── SKILL.md                  ← Skill 定义文档
```

## 技术栈

- **数据抓取**: Scrapling + BeautifulSoup4
- **雷达图**: Matplotlib（六边形极坐标）
- **画廊**: HTML + CSS + JavaScript（单文件，base64 嵌入图片）
- **飞书**: Webhook 交互式卡片 + lark_md 富文本
- **照片**: Pillow + Liquipedia Commons + 队名容错映射

## License

MIT
