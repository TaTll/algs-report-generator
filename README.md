# ALGS 赛事数据智能报告系统

> 🤖 AI Agent 驱动 | 抓取比赛数据、生成选手雷达图、构建数据网站、同步 GitHub Pages，并可生成剪映草稿工程。

线上网站：

https://TaTll.github.io/algs-report-generator/

## 项目在做什么

这个项目面向 ALGS 赛事数据内容生产，把 Apex Legends Status 的比赛页面转换成多种可用产物：

```text
Apex Legends Status 比赛页面
        ↓
Scrapling 动态抓取 Players Stats
        ↓
CSV 数据
        ↓
Matplotlib 六边形选手雷达图
        ↓
Markdown 预览 + HTML 画廊
        ↓
docs/ 静态网站
        ↓
GitHub Pages 上线
        ↓
可选：飞书通知 / 剪映工程草稿
```

当前网站包含：

- Group Stage：`ab`、`ac`、`ad`、`bc`、`bd`、`cd`
- Survivor Stage：`sf`
- Finals：`fn`
- Overall Standings / All Players 聚合视图

## 主要功能

- 🕷️ 使用 Scrapling 抓取动态比赛页面
- 📄 导出 `algs_players_data.csv`
- 📊 为每位选手生成六边形雷达图
- 🖼️ 生成交互式 HTML 画廊
- 🌐 构建 `docs/index.html` 静态数据网站
- 📮 可选：飞书 Webhook 推送战报卡片与 MD 预览
- 🎬 可选：生成剪映草稿工程，导入雷达图、选手照片和战队 Logo
- 🏷️ 内置战队名称容错映射与选手照片匹配

## 目录结构

```text
.
├─ build_app.py                 # 构建 GitHub Pages 静态网站
├─ docs/                        # GitHub Pages 输出目录
│  ├─ index.html
│  ├─ thumbs/                   # 雷达图缩略图
│  └─ photos/                   # 选手照片缩略图
├─ data/                        # 本地数据产物，默认不提交
│  ├─ fn/
│  ├─ sf/
│  └─ ...
└─ scripts/
   ├─ generate_report.py        # 抓取 → CSV → 雷达图 → MD → 画廊
   ├─ generate_algs_report.py   # 从 CSV 生成雷达图和基础 HTML 报告
   ├─ send_gallery.py           # 生成交互式画廊，可选飞书发送
   ├─ monitor_overview.py       # 监控 Overview 页面并处理新比赛
   ├─ team_utils.py             # 战队缩写、Logo、选手照片匹配
   ├─ build_jy_video.py         # 生成剪映草稿工程
   └─ update_all.py             # 一键更新网站并可提交推送
```

## 环境准备

推荐使用项目本地虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install "scrapling[all]" requests beautifulsoup4 pillow matplotlib numpy
.\.venv\Scripts\scrapling.exe install
```

如果要使用剪映工程生成功能，还需要安装 `jianying-editor` skill 及其依赖。当前脚本会按顺序查找：

1. 环境变量 `JY_SKILL_ROOT`
2. `%USERPROFILE%\.codex\skills\jianying-editor`
3. 旧 Reasonix 路径：`%APPDATA%\reasonix\skills\jianying-editor`

最小依赖示例：

```powershell
.\.venv\Scripts\python.exe -m pip install pymediainfo uiautomation pynput edge-tts imageio websockets
```

## 常用命令

### 更新单场比赛数据

```powershell
.\.venv\Scripts\python.exe scripts\generate_report.py "https://apexlegendsstatus.com/algs/Y6-Split1/ALGS-Playoffs/Global/Finals/Finals" --group fn --skip-feishu
```

产物会写入：

```text
data/fn/algs_players_data.csv
data/fn/radar_charts/
data/fn/preview.md
data/fn/radar_gallery.html
```

### 只用已有 CSV 重新生成图表和画廊

```powershell
.\.venv\Scripts\python.exe scripts\generate_report.py --group fn --skip-fetch --skip-feishu
```

### 重建网站

```powershell
.\.venv\Scripts\python.exe build_app.py
```

输出：

```text
docs/index.html
docs/thumbs/
docs/photos/
```

### 一键网站构建

```powershell
.\.venv\Scripts\python.exe scripts\update_all.py --website-only --skip-push
```

如需自动提交推送：

```powershell
.\.venv\Scripts\python.exe scripts\update_all.py --website-only
```

### 生成剪映草稿工程

全量生成某个阶段：

```powershell
.\.venv\Scripts\python.exe scripts\build_jy_video.py --group fn --name ALGS_Finals
```

只生成 1 个选手做小样测试：

```powershell
.\.venv\Scripts\python.exe scripts\build_jy_video.py --group fn --name ALGS_Finals_Test_1 --limit 1
```

按选手名筛选：

```powershell
.\.venv\Scripts\python.exe scripts\build_jy_video.py --group fn --name ALGS_WenXx_Test --player WenXx
```

剪映草稿默认写入剪映本地工程目录，例如：

```text
C:\Users\<User>\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft
```

## GitHub Pages

GitHub Pages 使用 `docs/` 目录作为静态站点来源。

上线流程：

```powershell
.\.venv\Scripts\python.exe build_app.py
git add docs build_app.py scripts .gitignore
git commit -m "Update ALGS data site"
git push origin main
```

访问：

https://TaTll.github.io/algs-report-generator/

## 注意事项

- `data/` 是本地中间产物，默认被 `.gitignore` 忽略。
- `docs/` 是线上网站产物，需要提交。
- `.venv/` 是本地虚拟环境，不要提交。
- `scripts/.feishu_config` 存放飞书 Webhook，已被忽略，不要提交。
- Windows 控制台建议使用 UTF-8；脚本已对常见 emoji 输出做了兼容处理。

## 技术栈

Python · Scrapling · Matplotlib · BeautifulSoup4 · Pillow · Feishu Webhook · JianYing Skill · GitHub Pages

## AI 协作模式

项目主要由 AI Agent 在 Human-in-the-loop 模式下迭代：用户用自然语言下达目标，Agent 负责拆解任务、生成代码、调试依赖、验证产物并协助上线。
