#!/usr/bin/env python3
"""
ALGS Player Data Parser & Hexagon Radar Chart Generator
读取页面数据 → CSV → 六边形雷达图
"""
import re, os, json, sys, csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patheffects as pe
import numpy as np
from math import pi

# ====== 1. Read data from CSV ======
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get('BH_DATA_DIR', os.path.join(BASE_DIR, '..', 'data'))
CSV_FILE = os.path.join(DATA_DIR, 'algs_players_data.csv')

sys.path.insert(0, BASE_DIR)
from team_utils import get_match_title
MATCH_TITLE, _ = get_match_title(CSV_FILE)
print(f"比赛: {MATCH_TITLE}")

players = []
with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        players.append(row)

print(f"从CSV读取到 {len(players)} 名选手数据")

# ====== 3. Generate Hexagon Radar Charts ======
OUT_DIR = os.path.join(DATA_DIR, 'radar_charts')
os.makedirs(OUT_DIR, exist_ok=True)

# 6-axis radar chart: KillParticipationPct, DmgDealt, KAD, Kills, Assists, KD
# Normalization: scale each metric to 0-100 for the radar
# hi 从数据动态计算（P75），让顶尖选手可以突破100%边界
_METRIC_DEFS = [
    ('KillParticipationPct', 'Kill\nParticipation%'),
    ('DmgDealt', 'Dmg\nDealt'),
    ('KAD', 'KA/D'),
    ('Kills', 'Kills'),
    ('Assists', 'Assists'),
    ('KD', 'K/D'),
]


def safe_float(val, default=0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _pctile(vals, p):
    """计算列表的第 p 百分位数"""
    if not vals:
        return 0
    s = sorted(vals)
    k = (len(s) - 1) * p / 100.0
    f = int(k)
    c = k - f
    if f + 1 < len(s):
        return s[f] + c * (s[f + 1] - s[f])
    return s[f]


def _build_radar_metrics(players):
    """根据选手数据动态计算每轴归一化上限：取排名第3的数值作为边界"""
    metrics = []
    for key, label in _METRIC_DEFS:
        raw_vals = [safe_float(p.get(key, 0)) for p in players]
        s = sorted(raw_vals)
        hi = s[-3] if len(s) >= 3 else (s[-1] if s else 0)  # 第3高的值
        lo = 0
        # 避免 hi == lo 导致除零
        if hi <= lo:
            hi = lo + 1
        metrics.append((key, label, lo, hi))
        print(f"  雷达轴 {label.replace(chr(10),' ')}: lo={lo} hi={hi:.1f} (Top3边界)")
    return metrics

RADAR_METRICS = _build_radar_metrics(players)



def make_radar_chart(player_data, output_path, avg_values=None):
    """Generate a hexagon radar chart for one player."""
    values = []
    for key, _, lo, hi in RADAR_METRICS:
        raw_val = safe_float(player_data.get(key, 0))
        # Normalize to 0-100
        norm = ((raw_val - lo) / (hi - lo)) * 100 if hi > lo else 0
        norm = max(0, min(300, norm))  # 统一上限200%，超出圆形边界的部分自然溢出
        values.append(norm)

    # Close the polygon
    values_closed = values + [values[0]]

    # Angles for hexagon (6 sides)
    angles = [n / 6 * 2 * pi for n in range(6)]
    angles_closed = angles + [angles[0]]

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')
    ax.spines['polar'].set_linewidth(0.15)  # 外圈边框极细

    # 统一边界200%，不显示参考网格线，数据六边形自由延伸
    ax.set_ylim(0, 300)
    ax.set_yticks([])  # 隐藏径向刻度

    # Draw axis lines with parameter names at the outer rim
    ax.set_xticks(angles)
    labels = ax.set_xticklabels(['KP%', 'Dmg', 'KA/D', 'Kills', 'Assists', 'K/D'],
                                color='white', size=13, fontweight='bold')
    for label in labels:
        label.set_path_effects([pe.withStroke(linewidth=4, foreground='#0f0f23')])
        label.set_zorder(20)
    ax.tick_params(axis='x', pad=40)

    # --- Average data (yellow hexagon) drawn first (behind player data) ---
    if avg_values:
        avg_closed = avg_values + [avg_values[0]]
        ax.fill(angles_closed, avg_closed, alpha=0.25, color='#ffd700', zorder=1)
        ax.plot(angles_closed, avg_closed, color='#ffd700', linewidth=2.5,
                linestyle='--', marker='s', markersize=7,
                markerfacecolor='#ffd700', markeredgecolor='white', markeredgewidth=1.5, zorder=1)

    # --- Player data (blue hexagon) ---
    ax.fill(angles_closed, values_closed, alpha=0.3, color='#00d2ff', zorder=2)
    ax.plot(angles_closed, values_closed, color='#00d2ff', linewidth=2.5, marker='o',
            markersize=8, markerfacecolor='#00d2ff', markeredgecolor='white', markeredgewidth=1.5, zorder=2)

    # Title
    player_display = player_data.get('Player', 'Unknown')
    team = player_data.get('Team', '')
    best_p = player_data.get('BestP', '')
    kills = player_data.get('Kills', '0')
    dmg = player_data.get('DmgDealt', '0')

    ax.set_title(f'{player_display}\n{team} | Best: {best_p} | Kills: {kills} | Dmg: {dmg}',
                 color='white', fontsize=14, fontweight='bold', pad=30,
                 bbox=dict(boxstyle='round,pad=0.5', facecolor='#0f3460', edgecolor='#00d2ff', alpha=0.8))

    # Footer
    fig.text(0.5, 0.02, MATCH_TITLE,
             ha='center', color='#888', fontsize=10, fontstyle='italic')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"  已生成: {os.path.basename(output_path)}")

# Compute average values (normalized 0-100) across all players for each radar axis
avg_values = []
for key, _, lo, hi in RADAR_METRICS:
    raw_vals = [safe_float(p.get(key, 0)) for p in players]
    avg_raw = sum(raw_vals) / len(raw_vals) if raw_vals else 0
    avg_norm = ((avg_raw - lo) / (hi - lo)) * 100 if hi > lo else 0
    avg_norm = max(0, min(300, avg_norm))  # 统一上限
    avg_values.append(avg_norm)
print(f"\n平均雷达值: KP%={avg_values[0]:.0f} Dmg={avg_values[1]:.0f} KA/D={avg_values[2]:.0f} Kills={avg_values[3]:.0f} Assists={avg_values[4]:.0f} K/D={avg_values[5]:.0f}")

# Generate for all players
print(f"\n正在生成 {len(players)} 名选手的六边形雷达图...")
for p in players:
    name_slug = re.sub(r'[\\/:*?"<>| ]', '_', p.get('Player', 'unknown'))
    out_path = os.path.join(OUT_DIR, f'{name_slug}.png')
    make_radar_chart(p, out_path, avg_values)

# ====== 4. Also generate a summary HTML ======
HTML_FILE = os.path.join(DATA_DIR, 'algs_players_report.html')
with open(HTML_FILE, 'w', encoding='utf-8') as f:
    f.write('''<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8">
<title>''' + MATCH_TITLE + ''' 选手数据报告</title>
<style>
body { font-family: 'Segoe UI', Arial, sans-serif; background: #0f0f23; color: #eee; margin: 0; padding: 20px; }
h1 { color: #00d2ff; text-align: center; border-bottom: 2px solid #00d2ff; padding-bottom: 10px; }
h2 { color: #fff; margin-top: 30px; }
table { border-collapse: collapse; width: 100%; margin: 20px 0; font-size: 13px; }
th { background: #1a1a3e; color: #00d2ff; padding: 8px; text-align: left; border: 1px solid #333; }
td { padding: 6px 8px; border: 1px solid #333; }
tr:nth-child(even) { background: #1a1a2e; }
tr:hover { background: #16213e; }
.radar-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 15px; }
.radar-card { background: #1a1a2e; border-radius: 10px; padding: 10px; text-align: center; border: 1px solid #333; }
.radar-card img { width: 100%; max-width: 350px; border-radius: 8px; }
.radar-card .name { color: #00d2ff; font-weight: bold; margin-top: 8px; }
.radar-card .team { color: #aaa; font-size: 12px; }
.radar-legend { background: #16213e; border-radius: 10px; padding: 14px 18px; margin: 20px 0; border: 1px solid #0f3460; }
.radar-legend h3 { color: #00d2ff; font-size: 14px; margin: 0 0 10px; text-align: center; }
.radar-legend .axes { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px 18px; font-size: 13px; color: #ccc; }
.radar-legend .axes span { background: #0f3460; padding: 4px 12px; border-radius: 10px; white-space: nowrap; }
</style></head>
<body>
<h1>🏆 ''' + MATCH_TITLE + '''</h1>
<p style="text-align:center;color:#aaa;">共 ''' + str(len(players)) + ''' 名选手 | 数据来源: apexlegendsstatus.com</p>
<h2>📊 数据表格</h2>
<table><tr><th>#</th><th>Player</th><th>Group</th><th>Team</th><th>BestP</th><th>Games</th>
<th>Kills</th><th>Assists</th><th>KillPart%</th><th>Knocks</th><th>DmgDealt</th><th>K/D</th><th>KA/D</th></tr>\n''')
    for idx, p in enumerate(players, 1):
        f.write(f'<tr><td>{idx}</td><td>{p.get("Player","")}</td><td>{p.get("Group","")}</td>'
                f'<td>{p.get("Team","")}</td><td>{p.get("BestP","")}</td><td>{p.get("Games","")}</td>'
                f'<td>{p.get("Kills","")}</td><td>{p.get("Assists","")}</td>'
                f'<td>{p.get("KillParticipationPct","")}%</td><td>{p.get("Knocks","")}</td>'
                f'<td>{p.get("DmgDealt","")}</td><td>{p.get("KD","")}</td><td>{p.get("KAD","")}</td></tr>\n')
    f.write('</table>\n')

    f.write('<h2>📈 六边形雷达图</h2>\n'
           '<div class="radar-legend">\n'
           '  <h3>六边形雷达图 · 六轴含义</h3>\n'
           '  <div class="axes">\n'
           '    <span>① 击杀参与率 (KP%)</span><span>② 伤害 (Dmg)</span><span>③ KA/D</span>\n'
           '    <span>④ 击杀 (Kills)</span><span>⑤ 助攻 (Assists)</span><span>⑥ K/D</span>\n'
           '  </div>\n'
           '</div>\n'
           '<div class="radar-grid">\n')
    for p in players:
        name_slug = re.sub(r'[\\/:*?"<>| ]', '_', p.get('Player', 'unknown'))
        f.write(f'<div class="radar-card">'
                f'<img src="radar_charts/{name_slug}.png" alt="{p.get("Player","")}">'
                f'<div class="name">{p.get("Player","")}</div>'
                f'<div class="team">{p.get("Team","")} | Group {p.get("Group","")}</div>'
                f'</div>\n')
    f.write('</div>\n')
    f.write('</body></html>')

print(f"\nHTML 报告: {HTML_FILE}")
print(f"CSV 数据: {CSV_FILE}")
print(f"雷达图目录: {OUT_DIR}")
print("完成!")
