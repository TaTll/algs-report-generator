#!/usr/bin/env python3
"""
发送ALGS选手数据到飞书 Webhook
"""
import requests
import json
import os
import csv
import base64

WEBHOOK_URL = os.environ.get("FEISHU_WEBHOOK_URL", "")

# ====== 读取CSV数据 ======
CSV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'algs_players_data.csv')
players = []
with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        players.append(row)

print(f"读取到 {len(players)} 名选手数据")

# ====== 发送消息到飞书 ======
def send_feishu(msg):
    r = requests.post(WEBHOOK_URL, json=msg, timeout=15)
    result = r.json()
    print(f"飞书响应: {result}")
    return result.get('code') == 0

# ----- 1. 发送欢迎消息 -----
welcome_msg = {
    "msg_type": "interactive",
    "card": {
        "header": {
            "title": {"tag": "plain_text", "content": "🏆 ALGS Y6 Split1 季后赛 Day1 数据报告"},
            "template": "blue"
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**比赛**: ALGS Year 6 Split 1 Playoffs — Day 1 A vs B\n**数据来源**: apexlegendsstatus.com\n**共采集**: {len(players)} 名选手\n**生成时间**: 实时"
                }
            },
            {"tag": "hr"},
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "**📊 数据文件已生成**\n• 完整CSV数据表 → `algs_players_data.csv`\n• 60张个人六边形雷达图 → `radar_charts/` 目录\n• 综合HTML报告 → `algs_players_report.html`"
                }
            }
        ]
    }
}

print("发送欢迎消息...")
send_feishu(welcome_msg)

# ----- 2. 发送击杀榜 Top 10 -----
top_kills = sorted(players, key=lambda p: int(p.get('Kills', 0) or 0), reverse=True)[:10]
kills_lines = [f"**{'选手':<20} {'队伍':<16} {'击杀':<6} {'KA/D':<8} {'伤害':<8} {'参与率':<8}**"]
kills_lines.append("─" * 70)
for p in top_kills:
    name = p.get('Player', '')
    team = p.get('Team', '')
    kills = p.get('Kills', '0')
    kad = p.get('KAD', '0')
    dmg = p.get('DmgDealt', '0')
    kp = p.get('KillParticipationPct', '0')
    kills_lines.append(f"{name:<20} {team:<16} {kills:<6} {kad:<8} {dmg:<8} {kp}%")

# Split into chunks for card (Feishu has ~2000 char limit per text block)
# Use lark_md format
top_kills_md = ""
for p in top_kills:
    name = p.get('Player', '')
    team = p.get('Team', '')
    kills = p.get('Kills', '0')
    kad = p.get('KAD', '0')
    dmg = p.get('DmgDealt', '0')
    kp = p.get('KillParticipationPct', '0')
    top_kills_md += f"{kills}杀 — **{name}** ({team}) | KA/D: {kad} | 伤害: {dmg} | 参与率: {kp}%\n"

killboard_msg = {
    "msg_type": "interactive",
    "card": {
        "header": {
            "title": {"tag": "plain_text", "content": "🔫 击杀榜 Top 10"},
            "template": "indigo"
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": top_kills_md
                }
            }
        ]
    }
}

print("发送击杀榜...")
send_feishu(killboard_msg)

# ----- 3. 发送伤害榜 Top 10 -----
top_dmg = sorted(players, key=lambda p: int(p.get('DmgDealt', '0') or '0'), reverse=True)[:10]
top_dmg_md = ""
for p in top_dmg:
    name = p.get('Player', '')
    team = p.get('Team', '')
    kills = p.get('Kills', '0')
    dmg = p.get('DmgDealt', '0')
    kad = p.get('KAD', '0')
    kp = p.get('KillParticipationPct', '0')
    top_dmg_md += f"**{dmg}**伤害 — **{name}** ({team}) | 击杀: {kills} | KA/D: {kad} | 参与率: {kp}%\n"

dmg_msg = {
    "msg_type": "interactive",
    "card": {
        "header": {
            "title": {"tag": "plain_text", "content": "💥 伤害榜 Top 10"},
            "template": "red"
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": top_dmg_md
                }
            }
        ]
    }
}

print("发送伤害榜...")
send_feishu(dmg_msg)

# ----- 4. 发送KA/D榜 Top 10 -----
top_kad = sorted(players, key=lambda p: float(p.get('KAD', '0') or '0'), reverse=True)[:10]
top_kad_md = ""
for p in top_kad:
    name = p.get('Player', '')
    team = p.get('Team', '')
    kills = p.get('Kills', '0')
    dmg = p.get('DmgDealt', '0')
    kad = p.get('KAD', '0')
    kp = p.get('KillParticipationPct', '0')
    top_kad_md += f"KA/D **{kad}** — **{name}** ({team}) | 击杀: {kills} | 伤害: {dmg} | 参与率: {kp}%\n"

kad_msg = {
    "msg_type": "interactive",
    "card": {
        "header": {
            "title": {"tag": "plain_text", "content": "⚡ KA/D 榜 Top 10"},
            "template": "turquoise"
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": top_kad_md
                }
            }
        ]
    }
}

print("发送KA/D榜...")
send_feishu(kad_msg)

# ----- 5. 发送参与率榜 Top 10 -----
top_kp = sorted(players, key=lambda p: float(p.get('KillParticipationPct', '0') or '0'), reverse=True)[:10]
top_kp_md = ""
for p in top_kp:
    name = p.get('Player', '')
    team = p.get('Team', '')
    kills = p.get('Kills', '0')
    dmg = p.get('DmgDealt', '0')
    kad = p.get('KAD', '0')
    kp = p.get('KillParticipationPct', '0')
    top_kp_md += f"参与率 **{kp}%** — **{name}** ({team}) | 击杀: {kills} | 伤害: {dmg} | KA/D: {kad}\n"

kp_msg = {
    "msg_type": "interactive",
    "card": {
        "header": {
            "title": {"tag": "plain_text", "content": "🎯 击杀参与率榜 Top 10"},
            "template": "green"
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": top_kp_md
                }
            }
        ]
    }
}

print("发送参与率榜...")
send_feishu(kp_msg)

# ----- 6. 尝试发送雷达图 -----
# Feishu webhook 发送图片需要先上传获取 image_key
# 通过上传 API: POST https://open.feishu.cn/open-apis/im/v1/images
# 但需要 tenant_access_token，不能直接用 webhook
# 替代方案：将图片转成base64后通过卡片发送（Feishu不支持）
# 改为：发送 summary 说明图片位置

print("发送完成！")
