#!/usr/bin/env python3
"""
一站式 ALGS 数据报告生成器
用法: python generate_report.py <URL>
示例: python generate_report.py "https://apexlegendsstatus.com/algs/Y6-Split1/ALGS-Playoffs/Global/Day1/CvD"

流程: 抓取数据 → CSV → 雷达图 → HTML画廊 → PDF报告 → 飞书通知
"""
import sys, os, re, csv, io, json, base64, argparse
import requests

# 路径设置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
SCRIPTS_DIR = BASE_DIR

# 飞书 Webhook
WEBHOOK_URL = os.environ.get('FEISHU_WEBHOOK_URL', '')

# ====== 依赖检查 ======
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("请安装: pip install beautifulsoup4")
    sys.exit(1)

try:
    from fpdf import FPDF
except ImportError:
    print("请安装: pip install fpdf2")
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
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS_DIR, 'generate_algs_report.py')],
        capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=SCRIPTS_DIR
    )
    if result.returncode == 0: print('  完成')
    if result.returncode != 0:
        print(f"雷达图生成出错: {result.stderr[-300:]}")
        return False
    return True


# ====== 4. 生成PDF报告 (移动端友好, 使用fpdf2) ======
def generate_pdf(data_rows):
    """生成适合手机查看的PDF报告"""
    print("生成PDF报告...")

    # 中文/英文混合标题，使用内置字体即可
    chart_dir = os.path.join(DATA_DIR, 'radar_charts')

    # 准备雷达图缩略图（缩小到120x120以减少PDF体积）
    thumb_size = 120
    img_thumbs = {}
    for f in sorted(os.listdir(chart_dir)):
        if f.endswith('.png'):
            name_key = f.replace('.png', '')
            img = PILImage.open(os.path.join(chart_dir, f))
            img.thumbnail((thumb_size, thumb_size), PILImage.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, 'PNG')
            img_thumbs[name_key] = buf

    # 标题
    groups = sorted(set(r.get('Group', '') for r in data_rows if r.get('Group')))
    group_str = ' vs '.join(groups) if groups else ''
    title = f"ALGS Playoffs - {group_str}" if group_str else "ALGS Players Stats"

    # 创建PDF
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=8)

    # ---- 封面 ----
    pdf.add_page()
    pdf.set_fill_color(15, 15, 35)
    pdf.rect(0, 0, 210, 297, 'F')
    pdf.set_text_color(0, 210, 255)
    pdf.set_font('Helvetica', 'B', 22)
    pdf.cell(0, 15, title, align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_text_color(136, 136, 136)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 8, 'Data: apexlegendsstatus.com', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_text_color(255, 215, 0)
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, f'{len(data_rows)} Players', align='C', new_x="LMARGIN", new_y="NEXT")

    # ---- 数据表 ----
    pdf.add_page()
    pdf.set_fill_color(15, 15, 35)
    pdf.rect(0, 0, 210, 297, 'F')
    pdf.set_text_color(0, 210, 255)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, 'Data Summary', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # 表头
    col_widths = [8, 38, 30, 8, 10, 10, 18, 10, 10, 12]
    headers = ['#', 'Player', 'Team', 'G', 'K', 'A', 'Dmg', 'K/D', 'KA/D', 'KP%']
    pdf.set_fill_color(22, 33, 62)
    pdf.set_text_color(0, 210, 255)
    pdf.set_font('Helvetica', 'B', 7)
    for i, (h, w) in enumerate(zip(headers, col_widths)):
        pdf.cell(w, 5, h, border=0, fill=True, align='L' if i < 3 else 'C')
    pdf.ln()

    # 表体
    pdf.set_font('Helvetica', '', 6.5)
    for idx, p in enumerate(data_rows):
        fill = (idx % 2 == 0)
        if fill:
            pdf.set_fill_color(17, 17, 40)
        else:
            pdf.set_fill_color(15, 15, 35)
        pdf.set_text_color(220, 220, 220)
        vals = [
            str(idx+1),
            p.get('Player',''),
            p.get('Team','')[:16],
            p.get('Games',''),
            p.get('Kills',''),
            p.get('Assists',''),
            p.get('DmgDealt',''),
            p.get('KD',''),
            p.get('KAD',''),
            p.get('KillParticipationPct',''),
        ]
        for v, w in zip(vals, col_widths):
            pdf.cell(w, 4.2, v, border=0, fill=fill, align='L' if len(v) > 4 else 'C')
        pdf.ln()

    # ---- 选手卡片（每页4个: 2行x2列）----
    cards_per_page = 4  # 2x2
    cols_per_row = 2
    card_w = 90
    card_h = 62
    margin_x = 10
    margin_y_top = 12
    gap_x = 10
    gap_y = 6

    for page_start in range(0, len(data_rows), cards_per_page):
        pdf.add_page()
        pdf.set_fill_color(15, 15, 35)
        pdf.rect(0, 0, 210, 297, 'F')

        page_players = data_rows[page_start:page_start + cards_per_page]
        for i, p in enumerate(page_players):
            row = i // cols_per_row
            col = i % cols_per_row
            x = margin_x + col * (card_w + gap_x)
            y = margin_y_top + row * (card_h + gap_y)

            name = p.get('Player', '')
            name_slug = name.replace(' ', '_').replace('/', '_')
            # Clean filename chars
            name_slug = re.sub(r'[^a-zA-Z0-9_-]', '_', name_slug)
            team = p.get('Team', '')[:20]
            group = p.get('Group', '')
            kills = p.get('Kills', '0')
            dmg = p.get('DmgDealt', '0')
            kd = p.get('KD', '0')
            kad = p.get('KAD', '0')
            kp = p.get('KillParticipationPct', '0')
            assists = p.get('Assists', '0')

            # 卡片背景
            pdf.set_fill_color(26, 26, 46)
            pdf.set_draw_color(42, 42, 78)
            pdf.rect(x, y, card_w, card_h, style='DF')

            # 选手名 + 战队
            pdf.set_xy(x + 3, y + 2)
            pdf.set_text_color(0, 210, 255)
            pdf.set_font('Helvetica', 'B', 8)
            pdf.cell(card_w - 6, 4, name, align='L')
            pdf.set_xy(x + 3, y + 6)
            pdf.set_text_color(136, 136, 136)
            pdf.set_font('Helvetica', '', 6)
            pdf.cell(card_w - 6, 3, f'{team} (G{group})', align='L')

            # 雷达图缩略图
            thumb_buf = img_thumbs.get(name_slug)
            if thumb_buf:
                pdf.image(thumb_buf, x=x + 2, y=y + 10, w=thumb_size/4.5, h=thumb_size/4.5)

            # 右侧数据
            sx = x + 30
            sy = y + 10
            pdf.set_font('Helvetica', '', 5.5)
            stats = [
                ('Kills', kills), ('Assists', assists), ('Dmg', dmg),
                ('K/D', kd), ('KA/D', kad), ('KP%', kp+'%'),
            ]
            for si, (label, val) in enumerate(stats):
                col_i = si % 2
                row_i = si // 2
                dx = sx + col_i * 28
                dy = sy + row_i * 14
                pdf.set_xy(dx, dy)
                pdf.set_text_color(136, 136, 136)
                pdf.cell(12, 4, label, align='L')
                pdf.set_xy(dx, dy + 4)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font('Helvetica', 'B', 8)
                pdf.cell(12, 4, val, align='L')
                pdf.set_font('Helvetica', '', 5.5)

    # 保存
    pdf_path = os.path.join(DATA_DIR, 'algs_report.pdf')
    pdf.output(pdf_path)
    pdf_size = os.path.getsize(pdf_path) / (1024 * 1024)
    print(f"PDF已生成: {pdf_path} ({pdf_size:.1f} MB)")
    return pdf_path


# ====== 5. 生成画廊HTML ======
def generate_gallery_html():
    """调用 send_gallery.py 生成交互式画廊"""
    print("生成交互式画廊...")
    import subprocess
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS_DIR, 'send_gallery.py'), '--skip-feishu'],
        capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=SCRIPTS_DIR
    )
    if result.returncode == 0: print('  完成')

    gallery_path = os.path.join(DATA_DIR, 'radar_gallery.html')
    if os.path.exists(gallery_path):
        return gallery_path
    return None


# ====== 6. 发送飞书 ======
def send_to_feishu(gallery_path, pdf_path, player_count):
    """上传HTML和PDF到飞书群 + 发送通知"""
    if not WEBHOOK_URL:
        print("(未配置 FEISHU_WEBHOOK_URL，跳过飞书发送)")
        return
    print("发送飞书通知...")

    success = []

    # 发送PDF文件
    if pdf_path and os.path.exists(pdf_path):
        try:
            with open(pdf_path, 'rb') as f:
                r = requests.post(
                    WEBHOOK_URL,
                    files={'file': ('algs_report.pdf', f)},
                    data={'msg_type': 'file'},
                    timeout=60
                )
            print(f"PDF上传: {r.json()}")
            success.append('PDF')
        except Exception as e:
            print(f"PDF上传失败: {e}")

    # 发送HTML文件
    if gallery_path and os.path.exists(gallery_path):
        try:
            with open(gallery_path, 'rb') as f:
                r = requests.post(
                    WEBHOOK_URL,
                    files={'file': ('radar_gallery.html', f)},
                    data={'msg_type': 'file'},
                    timeout=120
                )
            print(f"HTML上传: {r.json()}")
            success.append('HTML画廊')
        except Exception as e:
            print(f"HTML上传失败: {e}")

    # 发送文字通知
    uploaded = '、'.join(success) if success else '文件上传失败'
    msg = {
        "msg_type": "text",
        "text": {
            "content": f"[OK] ALGS 选手数据报告已生成\n\n共 {player_count} 名选手\n[PDF] 已上传: {uploaded}"
        }
    }
    r = requests.post(WEBHOOK_URL, json=msg, timeout=15)
    print(f"飞书通知: {r.json()}")


# ====== 主流程 ======
def main():
    parser = argparse.ArgumentParser(description='ALGS 选手数据报告生成器')
    parser.add_argument('url', nargs='?', help='ApexLegendsStatus 比赛页面 URL')
    parser.add_argument('--skip-fetch', action='store_true', help='跳过抓取，使用已有CSV')
    parser.add_argument('--skip-pdf', action='store_true', help='跳过PDF生成')
    parser.add_argument('--skip-feishu', action='store_true', help='跳过飞书发送')
    args = parser.parse_args()

    if not args.skip_fetch:
        if not args.url:
            print("请提供URL或使用 --skip-fetch 跳过抓取")
            print("示例: python generate_report.py \"https://apexlegendsstatus.com/algs/...\"")
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

    if not args.skip_pdf:
        print("\nStep 4/5: 生成PDF报告...")
        pdf_path = generate_pdf(data_rows)
    else:
        pdf_path = None

    print("\nStep 5/5: 生成画廊HTML...")
    gallery_path = generate_gallery_html()

    if not args.skip_feishu:
        if not WEBHOOK_URL:
            print("(提示: 设置环境变量 FEISHU_WEBHOOK_URL 即可自动发送飞书通知)")
        send_to_feishu(gallery_path, pdf_path, len(data_rows))

    print("\n" + "=" * 50)
    print("[OK] 全部完成!")
    print(f"   CSV:     data/algs_players_data.csv")
    print(f"   雷达图:   data/radar_charts/ ({len(data_rows)} 张)")
    if pdf_path:
        print(f"   PDF:     data/algs_report.pdf")
    if gallery_path:
        print(f"   画廊:    data/radar_gallery.html")


if __name__ == '__main__':
    main()
