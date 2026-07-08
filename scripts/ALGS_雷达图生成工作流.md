# ALGS 选手雷达图生成工作流

> 从 CSV 数据生成六边形雷达图 PNG + 交互式 HTML 画廊 + 静态数据报告，并通过飞书机器人发送通知。  
> 确保每次生成的图表样式、颜色、布局完全一致。

---

## 目录

1. [环境依赖](#1-环境依赖)
2. [数据格式](#2-数据格式)
3. [生成流程](#3-生成流程)
4. [脚本说明](#4-脚本说明)
5. [雷达图设计规范](#5-雷达图设计规范)
6. [HTML 输出文件说明](#6-html-输出文件说明)
7. [定制与修改指南](#7-定制与修改指南)
8. [常见问题](#8-常见问题)

---

## 1. 环境依赖

```bash
pip install matplotlib pillow requests
```

Python 版本：3.9+（测试通过 3.14.1）

验证安装：

```bash
python -c "import matplotlib; import PIL; import requests; print('OK')"
```

---

## 2. 数据格式

### CSV 文件：`data/algs_players_data.csv`

必须是 **UTF-8 with BOM** (`utf-8-sig`) 编码，包含以下列：

| 列名 | 说明 | 雷达图使用 |
|------|------|------------|
| `Player` | 选手名称 | ✓（标题） |
| `Group` | 分组 (A/B) | 标签显示 |
| `Team` | 战队名称 | ✓（副标题） |
| `BestP` | 最佳排名 | 标题栏 |
| `Games` | 比赛场数 | 弹窗显示 |
| `Kills` | 击杀数 | ✓ **轴④** |
| `Assists` | 助攻数 | ✓ **轴⑤** |
| `KillParticipationPct` | 击杀参与率 (%) | ✓ **轴①** |
| `Knocks` | 击倒数 | 弹窗显示 |
| `TimesKnocked` | 被击倒数 | 弹窗显示 |
| `DmgDealt` | 造成伤害 | ✓ **轴②** |
| `DmgTaken` | 承受伤害 | 弹窗显示 |
| `DmgDiff` | 伤害差值 | 弹窗显示 |
| `DmgPerKill` | 每杀伤害 | 弹窗显示 |
| `RingDmg` | 毒圈伤害 | 弹窗显示 |
| `Rez` | 复活次数 | 弹窗显示 |
| `Rspn` | 重生次数 | 弹窗显示 |
| `KD` | 击杀/死亡比 | ✓ **轴⑥** |
| `KAD` | (击杀+助攻)/死亡比 | ✓ **轴③** |
| `Deaths` | 死亡数 | 弹窗显示 |
| `SurvTime` | 存活时间 | 弹窗显示 |

---

## 3. 生成流程

> 所有脚本位于 `scripts/` 目录，输入输出位于 `data/` 目录。
> 脚本自动从 `scripts/` 定位 `../data/`，无需设置环境变量。

按顺序执行：

### Step 1 — 生成雷达图 + 静态报告

```bash
cd scripts
python generate_algs_report.py
```

**输出（均在 `data/` 下）：**
| 文件 | 说明 |
|------|------|
| `radar_charts/*.png` | 每名选手一张 800×800 六边形雷达图 |
| `algs_players_report.html` | 静态数据报告（表格 + 雷达图网格） |

### Step 2 — 生成交互式画廊 + 飞书通知

```bash
cd scripts
python send_gallery.py
```

**输出（均在 `data/` 下）：**
| 文件 | 说明 |
|------|------|
| `radar_gallery.html` | 交互式画廊（内嵌 base64 图片，可离线使用） |
| `radar_collage.jpg` | 所有雷达图拼图 |

生成完毕后脚本会自动：
1. 将 `radar_gallery.html` 作为文件上传到飞书群
2. 发送一条文字通知告知生成完成

> **顺序不可颠倒**：Step 2 依赖 Step 1 生成的 `radar_charts/*.png` 和 `algs_players_data.csv`。

---

## 4. 脚本说明

### 4.1 `generate_algs_report.py`

**功能：** 从 CSV 读取数据 → 归一化 → 绘制雷达图 → 生成静态 HTML 报告。

**关键代码段落：**

```python
# 六轴定义（顺序不可改变）
#        CSV字段                 标签      归一化范围
RADAR_METRICS = [
    ('KillParticipationPct', '...', 0, 100),     # 轴① → 图片右侧
    ('DmgDealt',             '...', 0, 12000),   # 轴② → 图片右上
    ('KAD',                  '...', 0, 7),        # 轴③ → 图片左上
    ('Kills',                '...', 0, 20),       # 轴④ → 图片左侧
    ('Assists',              '...', 0, 20),       # 轴⑤ → 图片左下
    ('KD',                   '...', 0, 4),        # 轴⑥ → 图片右下
]
```

**可定制项：**

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `RADAR_METRICS` 的 `lo` / `hi` | 归一化上下界 | 见上表 |
| `dpi` | 图片分辨率 | 150 |
| `figsize` | 画布尺寸 | (8, 8) |

### 4.2 `send_gallery.py`

**功能：** 将雷达图转为 base64 → 生成内嵌图片的可离线 HTML → 合成拼图 → 飞书通知。

**关键设计决策：**

- **选手数据内嵌为 JSON**：避免 `fetch()` 在 `file://` 协议下被浏览器阻止。
- **图片 base64 内嵌**：缩略图 600×600，生成约 8MB 单文件 HTML，无需外部资源。
- **飞书通知**：生成完毕后自动上传 HTML 文件并发送完成通知，失败不影响本地 HTML 生成。

### 4.3 `generate_report.py`

**功能：** 一站式脚本——输入 URL → 自动执行抓取、CSV、雷达图、HTML画廊、PDF报告、飞书通知全流程。

**用法：**
```bash
cd scripts
python generate_report.py "<URL>" [--skip-fetch] [--skip-pdf] [--skip-feishu]
```

**PDF 设计：** 使用 fpdf2 生成，深色背景 + A4 竖版，包含封面、汇总数据表和选手卡片（每页 4 张，含雷达图缩略图 + 关键数据），适合手机阅读。

---

## 5. 雷达图设计规范

> 以下规范由 `make_radar_chart()` 函数实现，修改此处可统一所有图表。

### 5.1 配色

| 元素 | 颜色代码 | 说明 |
|------|----------|------|
| 背景 | `#1a1a2e` | 深蓝黑 |
| 网格线 | `#333` | 灰色同心圆 |
| 刻度文字 | `#666` | |
| **选手数据** | `#00d2ff` | 蓝色填充 `alpha=0.3`，实线 2.5pt，圆形标记 8px |
| **平均值** | `#ffd700` | 黄色填充 `alpha=0.25`，虚线 2.5pt，方形标记 7px |
| 轴参数名 | `white` | 13pt bold，向外偏移 20px |
| 标题背景 | `#0f3460` | 蓝色半透明 |
| 脚注 | `#888` | 灰色斜体 |

### 5.2 六轴布局

```
           KA/D               Dmg
              ┌─────────────┐
              │             │
     Kills ←──┤   六边形    ├──→ KP%
              │   雷达图    │
              │             │
              └─────────────┘
          Assists             K/D
```

| 轴编号 | 参数名 | 角度 | 位置 |
|--------|--------|------|------|
| ① | KP% | 0° (右) | 右侧 |
| ② | Dmg | 60° | 右上 |
| ③ | KA/D | 120° | 左上 |
| ④ | Kills | 180° (左) | 左侧 |
| ⑤ | Assists | 240° | 左下 |
| ⑥ | K/D | 300° | 右下 |

### 5.3 归一化公式

每个指标线性映射到 0–100：

```
norm = ((raw_val - lo) / (hi - lo)) × 100
norm = clamp(norm, 0, 100)
```

### 5.4 绘制顺序

1. 灰色网格背景
2. 黄色平均六边形（虚线 + 方形标记）— **先画，在下层**
3. 蓝色选手六边形（实线 + 圆形标记）— **后画，在上层**
4. 外围轴参数名
5. 标题栏（选手名 / 战队 / 击杀 / 伤害）
6. 页脚
7. **不显示**：雷达图中间无数值标签（已移除）

---

## 6. HTML 输出文件说明

### 6.1 `algs_players_report.html` （静态报告）

- 数据表格（21列全部数据）
- 六轴图例（中文说明）
- 雷达图网格（`radar_charts/*.png` 外链图片）
- **需要** `radar_charts/` 目录与 HTML 在同一文件夹（即都在 `data/` 下）

### 6.2 `radar_gallery.html` （交互式画廊）

- 卡片画廊（搜索筛选）
- 点击卡片打开详情弹窗：
  - 雷达大图 + 外围 6 轴标签（含数值）
  - 选手信息（名称、战队、分组、排名、场数、存活时间）
  - 15 项详细统计数据
  - 六轴含义图例
- **独立文件**：图片 base64 内嵌，数据 JSON 内嵌，双击即可使用
- 生成后自动上传到飞书群

---

## 7. 定制与修改指南

### 修改雷达图外观

编辑 `generate_algs_report.py` → `make_radar_chart()` 函数：

| 需求 | 修改位置 |
|------|----------|
| 改颜色 | `color='#00d2ff'` → 改为新颜色 |
| 改透明度 | `alpha=0.3` → 改为 0–1 |
| 改变线条样式 | `linestyle='--'` → 改为 `'-'` `':'` `'-.'` |
| 改标记形状 | `marker='o'` → 改为 `'s'` `'^'` `'D'` |
| 修改归一化范围 | `RADAR_METRICS` 的 `lo` / `hi` |
| 修改图片分辨率 | `dpi=150` → 改为 `dpi=200` |
| 修改图片尺寸 | `figsize=(8, 8)` → 改为其他尺寸 |

### 修改 HTML 弹窗样式

编辑 `send_gallery.py` → `<style>` 块和 `showDetail()` 函数：

| 需求 | 修改位置 |
|------|----------|
| 弹窗大小 | `.modal-box` 的 `max-width` |
| 雷达图大小 | `.modal-header .radar-wrapper img` 的 `width` |
| 标签位置 | `.radax-0` ~ `.radax-5` 的 `top`/`left`/`right`/`bottom` |
| 标签颜色 | `.radax` 的 `color` 和 `border` |
| 数值颜色 | `.radax .val` 的 `color` |
| 修改后重新生成 | 运行 `python send_gallery.py` |

### 新增/删除雷达轴

1. 修改 `generate_algs_report.py` 的 `RADAR_METRICS`（增删元组）
2. 修改 `angles = [n / 6 * 2 * pi ...]` 将 `6` 改为轴数
3. 修改 `ax.set_xticklabels([...])` 中标签列表
4. 修改 `send_gallery.py` 的 CSS `.radax-0`~`.radax-5` 和 `showDetail()` 中标签
5. 重新运行 Step 1 → Step 2

---

## 8. 常见问题

### Q1: 点击雷达图没反应？

**原因**：旧版 `radar_gallery.html` 使用 `fetch()` 加载 CSV，`file://` 协议被浏览器阻止。  
**解决**：当前版本已内嵌 JSON 数据。如果问题仍存在，确认你使用的是最新生成的 `radar_gallery.html`。

### Q2: 中文显示乱码？

**原因**：CSV 未用 UTF-8 BOM 编码，或 matplotlib 无中文字体。  
**解决**：
1. 确保 `algs_players_data.csv` 是 `utf-8-sig` 编码
2. 雷达图本身不含中文（轴标签为英文缩写），标题为 ASCII

### Q3: 重新生成后图片不一致？

**原因**：可能修改了归一化范围、配色、或 matplotlib 版本不同。  
**解决**：保持 `RADAR_METRICS` 的 `lo`/`hi` 不变，固定 matplotlib 版本 `pip install matplotlib==3.9`。

### Q4: 如何添加更多选手？

1. 在 `data/algs_players_data.csv` 末尾追加新行
2. 在 `scripts/` 目录下运行 `python generate_algs_report.py`（重新计算平均值）
3. 在 `scripts/` 目录下运行 `python send_gallery.py`（重新生成画廊并发送飞书通知）

## Q5: 如何更改赛季标题？

编辑 `scripts/send_gallery.py` 中 HTML 模板的标题文字（`<h1>` 和 `<title>` 标签处）。

---

## 附录：文件清单

```
项目目录/
├── scripts/                          # 所有脚本
│   ├── generate_algs_report.py       #   脚本1：雷达图 + 静态报告
│   ├── send_gallery.py               #   脚本2：交互式画廊 + 飞书通知
│   ├── send_feishu.py                #   辅助：飞书消息发送
│   └── ALGS_雷达图生成工作流.md      #   本文档
│
├── data/                             # 所有数据 & 输出
│   ├── algs_players_data.csv         #   输入：选手数据
│   ├── radar_charts/                 #   输出：60 张 PNG 雷达图
│   │   └── ...（共 60 张）
│   ├── algs_players_report.html      #   输出：静态数据报告
│   ├── radar_gallery.html            #   输出：交互式画廊（独立可用）
│   └── radar_collage.jpg             #   输出：雷达图拼图
│
├── public/                           # Web 项目（无关）
├── reasonix.toml
└── .reasonix/
```
