# ALGS Report Generator

One-click Apex Legends esports data reports: radar charts, HTML gallery, mobile PDF, and Feishu notifications.

## Install

```
pip install -r requirements.txt
scrapling install --force
```

## Configure Feishu (optional)

Windows: `set FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx`

Mac/Linux: `export FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx`

Skip this to generate local files only.

## Usage

### One-click generate
```
cd scripts
python generate_report.py "https://apexlegendsstatus.com/algs/Y6-Split1/ALGS-Playoffs/Global/Day1/CvD"
```
Options: --skip-fetch, --skip-pdf, --skip-feishu

### Auto-monitor
```
cd scripts
python monitor_overview.py
```

Setup daily scheduled task:
```
schtasks //create //tn ALGS_Monitor //tr "python path\to\monitor_overview.py" //sc daily //st 12:00 //f
```

## Output (in data/)

- algs_report.pdf - Mobile-friendly PDF (dark theme, player cards)
- radar_gallery.html - Interactive gallery (search, click-to-detail)
- radar_charts/*.png - 60 hexagon radar charts per match

## License

MIT
