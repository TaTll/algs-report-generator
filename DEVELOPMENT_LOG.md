# ALGS Report Generator — 开发全记录

> 基于 Reasonix AI Agent 框架，通过自然语言驱动 AI 完成从零到一的全栈项目开发。

---

## 项目概述

**目标**：输入 ApexLegendsStatus 比赛 URL，一键生成选手雷达图 HTML 画廊 + MD 数据报告 + 剪映视频工程，自动发送飞书通知。

**技术栈**：Python · Matplotlib · Scrapling · BeautifulSoup4 · 飞书 Webhook · 剪映自动化 API · Reasonix Skill 框架

**协作方式**：所有代码由 AI Agent 根据自然语言指令编写、调试、迭代，人类负责验收和提出修改意见。

---

## 第一阶段：项目启动 & 数据基础

### 1.1 初始需求
> "进入这个网址，把每一个战队的Logo下载下来，文件名命名为战队缩写"

**AI 完成**：
- 分析 Liquipedia 页面结构，解析 398 个 `<img>` 标签
- 过滤出 40 支战队 Logo（排除国旗、游戏图标等噪音）
- 构建队名 → 缩写映射（如 `Team Falcons` → `FLCN`）
- 自动下载原始高清 PNG 到 `data/picture-ab/`

### 1.2 扩展：选手照片爬取
> "帮我把每个队伍 active 队员的照片也下载下来"

**AI 完成**：
- 遍历 40 支战队页面，解析 Active Roster 区域
- 逐一访问 124 名选手的个人页面，匹配 headshot 照片
- 实现智能过滤：排除 lightmode/darkmode/图标/Logo，保留真实照片
- 成功下载 109 张真实头像 + 15 个占位符（选手无照片）

---

## 第二阶段：Skill 框架搭建

### 2.1 集成到 Reasonix Skill
> "在数据网站上增添功能：点击雷达图后显示选手照片；优化 skill 加入爬取功能"

**AI 完成**：
- 创建 `team_utils.py`：队名容错映射 + 选手照片查找 + Logo 查找 + 完整爬虫函数
- 修改 `send_gallery.py`：弹窗详情加入圆形选手照片（base64 嵌入），无照片显示占位符
- 修改 `generate_report.py`：PDF 卡片嵌入选手照片 + 战队 Logo，卡片尺寸自适应
- 更新 `SKILL.md` 文档

### 2.2 飞书集成
> "为什么我的飞书没有收到 PDF？"

**AI 诊断**：
- 发现 PDF 排版重写时，`send_to_feishu()` 和 `main()` 函数被截断删除 —— 紧急恢复
- 测试发现飞书 Webhook 不支持 file 类型（code 10208），且消息限制 30KB
- **解决方案**：改为交互式卡片 + MD 预览推送（lark_md 格式），PDF 超过限制则提示文件路径

### 2.3 MD 格式优化
> "这个 md 文件里的图片不显示"

**AI 诊断**：
- MD 中 `![photo](本地路径)` 飞书无法访问 → 去掉所有本地图片引用
- Markdown 表格在飞书 lark_md 中不支持 → 改为纯列表格式
- 最终格式：粗体标题 + 编号列表，飞书完美渲染

---

## 第三阶段：PDF → MD 转型 & 多组别管理

### 3.1 取消 PDF，改为 MD 主输出
> "取消生成 pdf，改为生成 md 文件"

**AI 完成**：
- 移除 `fpdf2` 依赖和 200+ 行 PDF 生成代码
- 将 `generate_md_preview` 升级为 `generate_md_report`（主输出）
- CLI 参数 `--skip-pdf` → `--skip-md`
- 更新文档

### 3.2 文件夹隔离
> "把不同组别的文件放在不同的文件夹里"

**AI 完成**：
- 重构目录：`data/ab/`、`data/cd/`、`data/bd/`、`data/ac/`
- 修改全部 4 个脚本支持 `BH_DATA_DIR` 环境变量和 `--group` 参数
- `picture-ab/` 保持共享

### 3.3 动态标题
> "你的网页标题又错了，更新一下"

**AI 诊断**：标题硬编码为 `Day1 A vs B`

**AI 完成**：
- 新增 `get_match_title()` 函数，从 CSV 的 Group 列自动推断标题
- 映射 `(B, D) → Day 2`、`(A, C) → Day 2`
- 修改 `send_gallery.py` 和 `generate_algs_report.py` 三处硬编码

---

## 第四阶段：剪映视频工程

### 4.1 初版实现
> "新建工程文件，把 ac 组的数据图和选手图片导入时间轴，每个 3 秒，配上选手名字幕"

**AI 遇到**：
- `pymediainfo` 未安装 → pip install
- `uiautomation` 未安装 → pip install
- 图片 segment 默认时长覆盖整个时间轴 → 需显式传 `duration="3s"`
- 剪映 emoji `✅` 导致 GBK 终端崩溃 → 修复 jy_wrapper 源码

**AI 完成**：
- 60 名选手 × 3 秒 = 180 秒工程，116 条视频 + 116 条字幕

### 4.2 布局优化
> "数据图和选手图片放在两个时间轴，一一对应"
> "新建时间轴把战队 Logo 导入"

**AI 完成**：
- 三轨道并行：Radar（上层 + 字幕）、Photo（中层）、Logo（下层）
- 同一选手三张图同时出现，时长从 6 分钟优化到 3 分钟

### 4.3 通用化
> "把这个步骤更新在 skill 里"

**AI 完成**：
- 创建 `build_jy_video.py`，支持 `--group` / `--name` / `--duration` 参数
- 更新 SKILL.md 新增「剪映工程生成」章节

---

## 第五阶段：GitHub 发布

### 5.1 仓库准备
> "把这个 skill 上传到 GitHub"

**AI 完成**：
- `git init` + `.gitignore`（排除 `data/`、`node_modules/`、`.feishu_config`）
- 安全审查：确认无 API 密钥泄露
- 中文 README 编写
- 提交并推送

### 5.2 持续更新
- 每次功能迭代后自动 commit + push

---

## 第六阶段：数据运营 & 文案生成

> "对这场比赛做一个评价用作抖音文案"  
> "重点关注 DCG、VKG、PXX 三支中国战队"  
> "排名是不是弄错了" → AI 重新抓取官方积分排名修正

**AI 完成**：
- 读取 CSV 数据，按击杀/伤害/KD 多维度分析
- 抓取 ApexLegendsStatus 官方 Scores 表格获取准确积分排名
- 生成抖音风格电竞文案（emoji + 数据 + 话题标签）

---

## 技术亮点

| 亮点 | 说明 |
|------|------|
| **AI Agent 全流程开发** | 所有代码由 AI 根据自然语言编写、调试、迭代，人类零手写代码 |
| **队名容错映射** | Liquipedia / ALS / CSV 三个数据源的队名格式不一致，通过精确匹配 + 模糊匹配 + 反向索引三级策略解决 |
| **飞书适配** | 绕过 Webhook 30KB/file 限制，改用 lark_md 卡片推送；处理 emoji 导致的 GBK 编码崩溃 |
| **剪映 API 集成** | 利用第三方 jy_wrapper 实现图片批量导入、多轨道管理、字幕生成 |
| **图片智能过滤** | 从 398 个 img 标签中精准识别战队 Logo 和选手照片，排除国旗/图标/特效等噪音 |
| **动态标题推断** | 从 CSV Group 字段自动推断 Day + 组别，避免硬编码 |

---

## 项目文件树

```
scripts/
├── generate_report.py        ← 主入口：抓取 → CSV → 雷达图 → MD → 飞书
├── generate_algs_report.py   ← 六边形雷达图生成
├── send_gallery.py           ← 交互式 HTML 画廊（含选手照片弹窗）
├── send_feishu.py            ← 飞书排行榜推送
├── team_utils.py             ← 队名映射 + 照片查找 + Liquipedia 爬虫
├── build_jy_video.py         ← 剪映视频工程生成
└── monitor_overview.py       ← Overview 自动监控
```

---

## 关键数据

- **开发周期**：1 天内完成核心功能，持续迭代 2 天
- **代码量**：约 2000 行 Python（全部 AI 生成）
- **AI 交互轮次**：约 50 轮自然语言指令
- **处理数据**：40 支战队 × 60 名选手 × 21 项指标
- **GitHub**：https://github.com/TaTll/algs-report-generator
