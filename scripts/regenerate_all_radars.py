#!/usr/bin/env python3
"""为所有组别重新生成 P75 边界雷达图"""
import sys, os, csv, re

# 必须在 import matplotlib 前设置
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from math import pi

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")


def safe_float(val, default=0):
    try: return float(val)
    except: return default


def pctile(vals, p):
    if not vals: return 0
    s = sorted(vals)
    k = (len(s) - 1) * p / 100.0
    f = int(k)
    c = k - f
    return s[f] + c * (s[f+1] - s[f]) if f+1 < len(s) else s[f]


METRIC_DEFS = [
    ("KillParticipationPct", "Kill\nParticipation%"),
    ("DmgDealt", "Dmg\nDealt"),
    ("KAD", "KA/D"),
    ("Kills", "Kills"),
    ("Assists", "Assists"),
    ("KD", "K/D"),
]
SHORT_LABELS = ["KP%", "Dmg", "KA/D", "Kills", "Assists", "K/D"]

GROUP_NAMES = {
    "ab": "Day1 A vs B", "ac": "Day2 A vs C", "bd": "Day2 B vs D",
    "bc": "Day3 B vs C", "ad": "Day3 A vs D", "cd": "Day1 C vs D",
    "sf": "Survivor Stage",
}


def build_metrics(players):
    """每轴取排名第3的数值作为归一化边界"""
    metrics = []
    for key, label in METRIC_DEFS:
        raw_vals = [safe_float(p.get(key, 0)) for p in players]
        s = sorted(raw_vals)
        hi = s[-3] if len(s) >= 3 else (s[-1] if s else 0)  # 第3高的值
        lo = 0
        if hi <= lo: hi = lo + 1
        metrics.append((key, label, lo, hi))
        print(f"  轴 {label.replace(chr(10),' ')}: lo={lo} hi={hi:.1f} (Top3)")
    return metrics


def make_chart(player, radar_metrics, avg_values, out_path, match_title):
    values = []
    for key, _, lo, hi in radar_metrics:
        raw = safe_float(player.get(key, 0))
        norm = ((raw - lo) / (hi - lo)) * 100 if hi > lo else 0
        norm = max(0, min(300, norm))  # 统一上限200%，超出圆形边界的部分自然溢出
        values.append(norm)

    values_closed = values + [values[0]]
    angles = [n / 6 * 2 * pi for n in range(6)]
    angles_closed = angles + [angles[0]]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    ax.spines["polar"].set_linewidth(0.15)  # 外圈边框极细
    # 统一边界200%，不显示参考网格线
    ax.set_ylim(0, 300)
    ax.set_yticks([])  # 隐藏径向刻度
    ax.set_xticks(angles)
    labels = ax.set_xticklabels(SHORT_LABELS, color="white", size=13, fontweight="bold")
    for label in labels:
        label.set_path_effects([pe.withStroke(linewidth=4, foreground="#0f0f23")])
        label.set_zorder(20)
    ax.tick_params(axis="x", pad=40)

    if avg_values:
        avg_closed = avg_values + [avg_values[0]]
        ax.fill(angles_closed, avg_closed, alpha=0.25, color="#ffd700", zorder=1)
        ax.plot(angles_closed, avg_closed, color="#ffd700", linewidth=2.5,
                linestyle="--", marker="s", markersize=7,
                markerfacecolor="#ffd700", markeredgecolor="white", markeredgewidth=1.5, zorder=1)

    ax.fill(angles_closed, values_closed, alpha=0.3, color="#00d2ff", zorder=2)
    ax.plot(angles_closed, values_closed, color="#00d2ff", linewidth=2.5, marker="o",
            markersize=8, markerfacecolor="#00d2ff", markeredgecolor="white", markeredgewidth=1.5, zorder=2)

    player_name = player.get("Player", "Unknown")
    team = player.get("Team", "")
    best_p = player.get("BestP", "")
    kills = player.get("Kills", "0")
    dmg = player.get("DmgDealt", "0")
    ax.set_title(f"{player_name}\n{team} | Best: {best_p} | Kills: {kills} | Dmg: {dmg}",
                 color="white", fontsize=14, fontweight="bold", pad=30,
                 bbox=dict(boxstyle="round,pad=0.5", facecolor="#0f3460", edgecolor="#00d2ff", alpha=0.8))
    fig.text(0.5, 0.02, match_title, ha="center", color="#888", fontsize=10, fontstyle="italic")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()


def main():
    for group, label in sorted(GROUP_NAMES.items()):
        csv_path = os.path.join(DATA_DIR, group, "algs_players_data.csv")
        radar_dir = os.path.join(DATA_DIR, group, "radar_charts")
        if not os.path.exists(csv_path):
            print(f"跳过 {group}: 无 CSV")
            continue
        os.makedirs(radar_dir, exist_ok=True)

        players = []
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                players.append(row)

        match_title = f"ALGS Y6 Split1 Playoffs - {label}"
        print(f"\n=== {group.upper()} ({len(players)} 选手) ===")

        metrics = build_metrics(players)
        avg_values = []
        for key, _, lo, hi in metrics:
            raw_vals = [safe_float(p.get(key, 0)) for p in players]
            avg_raw = sum(raw_vals) / len(raw_vals)
            avg_norm = ((avg_raw - lo) / (hi - lo)) * 100 if hi > lo else 0
            avg_norm = max(0, min(300, avg_norm))  # 统一上限
            avg_values.append(avg_norm)

        for p in players:
            slug = re.sub(r'[\\/:*?"<>| ]', "_", p.get("Player", "unknown"))
            out_path = os.path.join(radar_dir, f"{slug}.png")
            make_chart(p, metrics, avg_values, out_path, match_title)

        print(f"  完成: {len(players)} 张")
    print("\n全部组别雷达图已更新!")


if __name__ == "__main__":
    main()
