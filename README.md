# ALGS 数据报告生成器

> 输入 [ApexLegendsStatus](https://apexlegendsstatus.com) 比赛 URL，一键生成选手六边形雷达图、交互式 HTML 画廊、MD 数据报告，自动发送飞书通知。

## 功能

| 功能 | 说明 |
|------|------|
| 🕷️ 数据抓取 | Scrapling 自动抓取 ApexLegendsStatus 选手数据 |
| 📊 雷达图 | 60 张六边形雷达图，含全选手平均对比 |
| 🖼️ 画廊 | HTML 页面，搜索筛选 + 弹窗详情 + 选手照片 + 战队 Logo |
| 📝 MD 报告 | Top 10 伤害榜 + 战队排名（飞书 lark_md 格式） |
| 📮 飞书通知 | 摘要卡片 + MD 数据预览自动推送 |
| 🤖 自动监控 | 每天 12:00 检查 Overview，新比赛自动生成 |
| 🏷️ 战队映射 | 容错匹配各种队名变体（如 `AURORA`→`AUR`） |
| 📷 照片爬取 | 从 Liquipedia 下载 40 队 Logo + 120+ 选手照片 |

## 快速开始

### 1. 安装依赖

```bash
pip install "scrapling[all]>=0.4.10" beautifulsoup4 matplotlib pillow requests
scrapling install --force
```

### 2. 爬取战队 Logo 和选手照片（首次）

```bash
cd scripts
python -c "from team_utils import crawl_team_logos_and_photos; crawl_team_logos_and_photos()"
```

图片保存至 `data/picture-ab/`。

### 3. 生成报告

```bash
cd scripts
python generate_report.py "https://apexlegendsstatus.com/algs/Y6-Split1/ALGS-Playoffs/Global/Day2/BvD" --group bd
```

| 参数 | 说明 |
|------|------|
| `--group bd` | 输出到 `data/{group}/` 子目录 |
| `--skip-fetch` | 跳过抓取，使用已有 CSV |
| `--skip-md` | 跳过 MD 报告生成 |
| `--skip-feishu` | 跳过飞书发送 |

### 4. 配置飞书（可选）

```bash
echo "https://open.feishu.cn/open-apis/bot/v2/hook/xxx" > scripts/.feishu_config
```

Webhook URL 从飞书群 → 设置 → 机器人 → 自定义机器人获取。

### 5. 自动监控

```bash
cd scripts
python monitor_overview.py          # 单次检查
python monitor_overview.py --watch  # 每 30 分钟循环
```

## 输出

```
data/{group}/
├── algs_players_data.csv     ← 选手数据
├── radar_charts/             ← N 张雷达图 PNG
├── radar_gallery.html        ← 交互式画廊
├── preview.md                ← MD 数据报告
└── radar_collage.jpg         ← 拼图
```

## 单独使用子模块

```bash
# 只重新生成画廊
BH_DATA_DIR="../data/bd" python send_gallery.py --skip-feishu

# 只重新生成雷达图
BH_DATA_DIR="../data/bd" python generate_algs_report.py
```

## 文件说明

| 文件 | 作用 |
|------|------|
| `generate_report.py` | 主入口，串联全流程 |
| `generate_algs_report.py` | 读取 CSV 生成六边形雷达图 |
| `send_gallery.py` | 生成交互式 HTML 画廊（嵌入图片和照片） |
| `send_feishu.py` | 发送飞书排行榜卡片 |
| `team_utils.py` | 战队名映射 + 选手照片查找 + Liquipedia 爬虫 |
| `monitor_overview.py` | Overview 页面自动监控 |
