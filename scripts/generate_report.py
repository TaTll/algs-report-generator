#!/usr/bin/env python3
"""
一站式 ALGS 数据报告生成器
用法: python generate_report.py <URL> --group bd
示例: python generate_report.py "https://apexlegendsstatus.com/algs/Y6-Split1/ALGS-Playoffs/Global/Day2/BvD" --group bd

流程: 抓取数据 → CSV → 雷达图 → HTML画廊 → PDF报告 → 飞书通知
"""
import sys, os, re, csv, io, json, base64, argparse
import requests

# 路径设置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
SCRIPTS_DIR = BASE_DIR

# 飞书 Webhook
WEBHOOK_URL = os.environ.get('FEISHU_WEBHOOK_URL', '')
# 如果环境变量未设置，尝试从配置文件读取
if not WEBHOOK_URL:
    config_file = os.path.join(BASE_DIR, '.feishu_config')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            WEBHOOK_URL = f.read().strip()
        os.environ['FEISHU_WEBHOOK_URL'] = WEBHOOK_URL

# 导入战队映射和选手照片工具
sys.path.insert(0, BASE_DIR)
from team_utils import find_player_photo, get_player_photo_base64, get_team_abbr, find_team_logo, get_match_title
PICTURE_DIR = os.path.join(ROOT_DATA_DIR, 'picture-ab')

# DATA_DIR: 优先从环境变量读取（子进程调用），否则用根目录
DATA_DIR = os.environ.get('BH_DATA_DIR', ROOT_DATA_DIR)
GROUP = None

# ====== 依赖检查 ======
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("请安装: pip install beautifulsoup4")
    sys.exit(1)

from PIL import Image as PILImage

import matplotlib
matplotlib.use('Agg')

# ====== 1. 抓取数据 ======
def fetch_player_data(url):
    """用 Scrapling 抓取页面，提取 Players Stats 表格数据"""
    print(f"正在抓取: {url}")

    # 确保URL包含正确的fragment
    if '#tab_' not in url:
        url = url.rstrip('/') + '#tab_playersstats'

    # 使用 Scrapling CLI 抓取
    import subprocess, tempfile
    html_path = os.path.join(DATA_DIR, '_fetch_temp.html')

    cmd = [
        'scrapling', 'extract', 'fetch', url,
        html_path,
        '--network-idle', '--timeout', '60000'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=DATA_DIR)
    print(result.stdout[-200:] if len(result.stdout) > 200 else result.stdout)

    if not os.path.exists(html_path):
        print(f"抓取失败，输出文件未生成")
        return None

    # 如果scores tab被加载（默认），需要重新请求playersstats
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')
    players_div = soup.find('div', id='playersstats-content')
    if not players_div:
        print("错误: 未找到 playersstats-content div，数据可能为空")
        os.remove(html_path)
        return None

    table = players_div.find('table', {'data-column-manager': 'players-stats'})
    if not table:
        print("错误: 未找到 players stats 表格")
        os.remove(html_path)
        return None

    rows = table.find_all('tr')
    html_headers = []
    for th in rows[0].find_all('th'):
        h = th.get_text(strip=True).replace('\u2013', '-').replace('\u2192', '->')
        html_headers.append(h)

    COL_MAP = {
        'Player': 'Player', 'Team': 'Team', 'Best P.': 'BestP', 'Games': 'Games',
        'Kills': 'Kills', 'Assists': 'Assists', 'Kill Participation%': 'KillParticipationPct',
        'Knocks': 'Knocks', 'Times knocked': 'TimesKnocked',
        'Dmg dealt': 'DmgDealt', 'Dmg taken': 'DmgTaken', 'Dmg diff': 'DmgDiff',
        'Dmg/kill': 'DmgPerKill', 'Ring dmg': 'RingDmg',
        'Rez.': 'Rez', 'Rspn.': 'Rspn', 'K/D': 'KD', 'KA/D': 'KAD',
        'Deaths': 'Deaths', 'Surv. time': 'SurvTime',
    }

    out_cols = ['Player', 'Group', 'Team', 'BestP', 'Games', 'Kills', 'Assists',
        'KillParticipationPct', 'Knocks', 'TimesKnocked', 'DmgDealt', 'DmgTaken',
        'DmgDiff', 'DmgPerKill', 'RingDmg', 'Rez', 'Rspn', 'KD', 'KAD', 'Deaths', 'SurvTime']

    data_rows = []
    for row in rows[1:]:
        cells = row.find_all('td')
        if not cells:
            continue
        row_data = {}
        for i, cell in enumerate(cells):
            if i >= len(html_headers):
                break
            html_col = html_headers[i]
            if html_col not in COL_MAP:
                continue
            out_col = COL_MAP[html_col]
            if html_col == 'Player':
                link = cell.find('a', class_='algs-player-page-link')
                row_data['Player'] = link.get_text(strip=True) if link else cell.get_text(strip=True)
                group_span = cell.find('span', class_='team-group-square')
                row_data['Group'] = group_span.get_text(strip=True) if group_span else ''
            elif html_col in ('Dmg dealt', 'Dmg taken'):
                row_data[out_col] = cell.get_text(strip=True).replace(',', '')
            else:
                row_data[out_col] = cell.get_text(strip=True)
        if row_data:
            data_rows.append(row_data)

    os.remove(html_path)
    return data_rows, out_cols


# ====== 2. 生成CSV ======
def save_csv(data_rows, out_cols):
    csv_path = os.path.join(DATA_DIR, 'algs_players_data.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=out_cols)
        writer.writeheader()
        writer.writerows(data_rows)
    return csv_path


# ====== 3. 生成雷达图 (调用 generate_algs_report) ======
def generate_radar_charts():
    """调用 generate_algs_report.py 生成雷达图"""
    print("生成雷达图...")
    import subprocess
    env = os.environ.copy()
    env['BH_DATA_DIR'] = DATA_DIR
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS_DIR, 'generate_algs_report.py')],
        capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=SCRIPTS_DIR,
        env=env
    )
    if result.returncode == 0: print('  完成')
    if result.returncode != 0:
        print(f"雷达图生成出错: {result.stderr[-300:]}")
        return False
    return True


# ====== 5. 生成画廊HTML ======


# ====== 4. 生成MD报告 ======
def generate_md_report(data_rows):
    """生成 Markdown 格式的数据报告（主输出 + 飞书发送）"""
    print("生成MD报告...")
    
    title, _ = get_match_title(os.path.join(DATA_DIR, 'algs_players_data.csv'))
    
    # Sort by damage
    sorted_players = sorted(data_rows, key=lambda p: int(p.get('DmgDealt', '0') or '0'), reverse=True)
    
    # Team summary
    teams = {}
    for p in data_rows:
        t = p.get('Team', 'Unknown')
        if t not in teams:
            teams[t] = {'total_kills': 0, 'total_dmg': 0}
        teams[t]['total_kills'] += int(p.get('Kills', '0') or '0')
        teams[t]['total_dmg'] += int(p.get('DmgDealt', '0') or '0')
    teams_sorted = sorted(teams.items(), key=lambda x: x[1]['total_dmg'], reverse=True)
    
    # Feishu lark_md doesn't support tables, use list format
    md = []
    md.append(f"**{title}** — {len(data_rows)} players · {len(teams)} teams")
    md.append("")
    md.append("**Top 10 Damage**")
    for i, p in enumerate(sorted_players[:10]):
        md.append(f"{i+1}. **{p['Player']}** ({p['Team']}) K:{p.get('Kills','0')} A:{p.get('Assists','0')} Dmg:{p.get('DmgDealt','0')} KD:{p.get('KD','0')} KAD:{p.get('KAD','0')}")
    md.append("")
    md.append("**Team Rankings**")
    for i, (tname, td) in enumerate(teams_sorted):
        md.append(f"{i+1}. **{tname}** — {td['total_kills']}K / {td['total_dmg']:,} dmg")
    
    md_path = os.path.join(DATA_DIR, 'preview.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(chr(10).join(md))
    print(f"MD报告: {md_path} ({os.path.getsize(md_path)} bytes)")
    return md_path


def generate_gallery_html():
    """调用 send_gallery.py 生成交互式画廊"""
    print("生成交互式画廊...")
    import subprocess
    env = os.environ.copy()
    env['BH_DATA_DIR'] = DATA_DIR
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS_DIR, 'send_gallery.py'), '--skip-feishu'],
        capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=SCRIPTS_DIR,
        env=env
    )
    if result.returncode == 0: print('  完成')

    gallery_path = os.path.join(DATA_DIR, 'radar_gallery.html')
    if os.path.exists(gallery_path):
        return gallery_path
    return None


# ====== 6. 发送飞书 ======
def send_to_feishu(gallery_path, md_path, player_count):
    """发送飞书通知：交互式卡片 + 小文件尝试上传，大文件提示路径"""
    if not WEBHOOK_URL:
        print("(未配置 FEISHU_WEBHOOK_URL，跳过飞书发送)")
        return
    print("发送飞书通知...")

    # 收集报告摘要信息
    teams = set()
    for p in (data_rows if 'data_rows' in dir() else []):
        teams.add(p.get('Team', ''))
    
    # 读取 CSV 获取小组信息
    groups = set()
    csv_path = os.path.join(DATA_DIR, 'algs_players_data.csv')
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                groups.add(row.get('Group', ''))
    group_str = ' vs '.join(sorted(groups)) if groups else '?'

    # ---- 交互式卡片 ----
    title, _ = get_match_title(csv_path) if os.path.exists(csv_path) else ('ALGS Report', '')
    
    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"ALGS — {title}"},
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": f"**{player_count} Players · {len(teams)} Teams · 6 Games**\nData: apexlegendsstatus.com"}
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": f"📁 **文件已生成**\n• 画廊: `data/{GROUP + '/' if GROUP else ''}radar_gallery.html`\n• PDF: `data/{GROUP + '/' if GROUP else ''}algs_report.pdf`\n• 雷达图: `data/{GROUP + '/' if GROUP else ''}radar_charts/` ({player_count}张)"}
                },
                {"tag": "hr"},
                {
                    "tag": "note",
                    "elements": [{"tag": "plain_text", "content": "PDF超过30KB限制，请从服务器获取。提供飞书App凭证可启用自动上传。"}]
                }
            ]
        }
    }

    r = requests.post(WEBHOOK_URL, json=card, timeout=15)
    result = r.json()
    print(f"飞书卡片: {result.get('code', '?')} - {result.get('msg', '?')}")
    
    # ---- 发送 MD 预览 ----
    md_path = os.path.join(DATA_DIR, 'preview.md')
    if os.path.exists(md_path):
        try:
            with open(md_path, 'r', encoding='utf-8') as mf:
                md_content = mf.read()
            
            # Split into lark_md chunks (max ~1900 chars each)
            chunks = []
            cur = ""
            for line in md_content.split(chr(10)):
                if len(cur) + len(line) > 1800:
                    chunks.append(cur)
                    cur = line + chr(10)
                else:
                    cur += line + chr(10)
            if cur:
                chunks.append(cur)
            
            # Build card elements (max 45)
            elems = [{
                "tag": "div",
                "text": {"tag": "lark_md", "content": chunk}
            } for chunk in chunks[:45]]
            
            md_card = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {"tag": "plain_text", "content": f"MD Preview - {title}"},
                        "template": "turquoise"
                    },
                    "elements": elems
                }
            }
            r = requests.post(WEBHOOK_URL, json=md_card, timeout=15)
            print(f"MD预览发送: {r.json().get('code')} - {r.json().get('msg')}")
        except Exception as e:
            print(f"MD预览发送失败: {e}")
    else:
        print(f"(MD预览文件不存在: {md_path})")


# ====== 主流程 ======
def main():
    parser = argparse.ArgumentParser(description='ALGS 选手数据报告生成器')
    parser.add_argument('url', nargs='?', help='ApexLegendsStatus 比赛页面 URL')
    parser.add_argument('--group', '-g', default=None, help='输出子目录名 (如 bd, ab, cd)')
    parser.add_argument('--skip-fetch', action='store_true', help='跳过抓取，使用已有CSV')
    parser.add_argument('--skip-md', action='store_true', help='跳过MD报告生成')
    parser.add_argument('--skip-feishu', action='store_true', help='跳过飞书发送')
    args = parser.parse_args()

    # 设置输出目录
    global DATA_DIR, GROUP
    if args.group:
        GROUP = args.group.lower()
        DATA_DIR = os.path.join(ROOT_DATA_DIR, GROUP)
    else:
        DATA_DIR = ROOT_DATA_DIR
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f'输出目录: {DATA_DIR}')

    if not args.skip_fetch:
        if not args.url:
            print("请提供URL或使用 --skip-fetch 跳过抓取")
            print("Usage: python generate_report.py <URL>")
            sys.exit(1)

        print("=" * 50)
        print("Step 1/5: 抓取数据...")
        result = fetch_player_data(args.url)
        if not result:
            print("数据抓取失败!")
            sys.exit(1)
        data_rows, out_cols = result
        print(f"抓取到 {len(data_rows)} 名选手数据")

        print("\nStep 2/5: 保存CSV...")
        csv_path = save_csv(data_rows, out_cols)
        print(f"CSV已保存: {csv_path}")
    else:
        # 从已有CSV读取
        csv_path = os.path.join(DATA_DIR, 'algs_players_data.csv')
        if not os.path.exists(csv_path):
            print(f"CSV文件不存在: {csv_path}")
            sys.exit(1)
        data_rows = []
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data_rows.append(row)
        print(f"从已有CSV读取到 {len(data_rows)} 名选手")

    print("\nStep 3/5: 生成雷达图...")
    if not generate_radar_charts():
        print("雷达图生成失败!")
        sys.exit(1)

    if not args.skip_md:
        print("\nStep 4/5: 生成MD报告...")
        md_path = generate_md_report(data_rows)
    else:
        md_path = None

    print("\nStep 5/5: 生成画廊HTML...")
    gallery_path = generate_gallery_html()

    if not args.skip_feishu:
        if not WEBHOOK_URL:
            print("(提示: 设置环境变量 FEISHU_WEBHOOK_URL 即可自动发送飞书通知)")
        else:
            send_to_feishu(gallery_path, md_path, len(data_rows))

    print("\n" + "=" * 50)
    print("[OK] 全部完成!")
    print(f"   CSV:     data/{GROUP + '/' if GROUP else ''}algs_players_data.csv")
    print(f"   雷达图:   data/{GROUP + '/' if GROUP else ''}radar_charts/ ({len(data_rows)} 张)")
    if md_path:
        print(f"   MD:      data/{GROUP + '/' if GROUP else ''}preview.md")
    if gallery_path:
        print(f"   画廊:    data/{GROUP + '/' if GROUP else ''}radar_gallery.html")


if __name__ == '__main__':
    main()
