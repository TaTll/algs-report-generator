#!/usr/bin/env python3
"""
ALGS 数据网站构建器
扫描各组 CSV → 生成 JSON → 注入单文件 HTML → 输出到 public/
"""
import os, csv, json, sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
os.makedirs(PUBLIC_DIR, exist_ok=True)

# ====== 1. 扫描数据 ======
groups = {
    "ab": {"label": "Day1 A vs B"},
    "ac": {"label": "Day2 A vs C"},
    "bd": {"label": "Day2 B vs D"},
    "cd": {"label": "Day1 C vs D"},
}

all_data = {}
for g, info in groups.items():
    csv_path = os.path.join(DATA_DIR, g, "algs_players_data.csv")
    if not os.path.exists(csv_path):
        continue

    rows = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows.append(r)

    # Team stats
    teams = {}
    for r in rows:
        t = r["Team"]
        if t not in teams:
            teams[t] = {"k": 0, "d": 0, "group": r.get("Group", "")}
        teams[t]["k"] += int(r.get("Kills", "0") or "0")
        teams[t]["d"] += int(r.get("DmgDealt", "0") or "0")

    # Player stats sorted by damage
    players_sorted = sorted(rows, key=lambda x: int(x.get("DmgDealt", "0") or "0"), reverse=True)

    all_data[g] = {
        "label": info["label"],
        "player_count": len(rows),
        "team_count": len(teams),
        "groups": sorted(set(r.get("Group", "") for r in rows)),
        "top_kills": [
            {"name": p["Player"], "team": p["Team"], "kills": p.get("Kills", "0"),
             "dmg": p.get("DmgDealt", "0"), "kd": p.get("KD", "0"), "kad": p.get("KAD", "0")}
            for p in sorted(rows, key=lambda x: int(x.get("Kills", "0") or "0"), reverse=True)[:5]
        ],
        "top_dmg": [
            {"name": p["Player"], "team": p["Team"], "dmg": p.get("DmgDealt", "0"),
             "kills": p.get("Kills", "0"), "kd": p.get("KD", "0")}
            for p in sorted(rows, key=lambda x: int(x.get("DmgDealt", "0") or "0"), reverse=True)[:5]
        ],
        "teams": [
            {"name": t, "kills": td["k"], "dmg": td["d"], "group": td["group"]}
            for t, td in sorted(teams.items(), key=lambda x: x[1]["k"], reverse=True)
        ],
        "players": [
            {"name": p["Player"], "team": p["Team"], "group": p.get("Group", ""),
             "kills": p.get("Kills", "0"), "assists": p.get("Assists", "0"),
             "dmg": p.get("DmgDealt", "0"), "kd": p.get("KD", "0"),
             "kad": p.get("KAD", "0"), "kp": p.get("KillParticipationPct", "0"),
             "bestp": p.get("BestP", ""), "games": p.get("Games", "0")}
            for p in players_sorted
        ],
    }

json_str = json.dumps(all_data, ensure_ascii=False)

# ====== 2. HTML 模板 ======
html = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ALGS Y6 Split1 Playoffs — 数据报告</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,'Segoe UI',Arial,sans-serif;background:#0a0a1a;color:#ccc;min-height:100vh}
.header{background:linear-gradient(135deg,#0f0f2e,#1a1040);padding:24px;text-align:center;border-bottom:2px solid #1a1a4e}
.header h1{color:#00d2ff;font-size:clamp(18px,4vw,28px);margin-bottom:6px}
.header p{color:#888;font-size:14px}
.tabs{display:flex;justify-content:center;gap:8px;padding:16px;flex-wrap:wrap}
.tab-btn{background:#14142e;color:#888;border:1px solid #2a2a4e;padding:8px 20px;border-radius:20px;cursor:pointer;font-size:14px;transition:all .2s}
.tab-btn:hover{color:#00d2ff;border-color:#00d2ff}
.tab-btn.active{background:#00d2ff;color:#0a0a1a;border-color:#00d2ff;font-weight:bold}
.content{max-width:1200px;margin:0 auto;padding:0 16px 40px}
.tab-panel{display:none}
.tab-panel.active{display:block}
.stats-bar{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}
.stat-box{background:#14142e;border:1px solid #2a2a4e;border-radius:10px;padding:12px 16px;flex:1;min-width:120px;text-align:center}
.stat-box .num{color:#00d2ff;font-size:22px;font-weight:bold}
.stat-box .lbl{color:#666;font-size:12px;margin-top:2px}
.section-title{color:#00d2ff;font-size:18px;margin:24px 0 12px;padding-bottom:8px;border-bottom:1px solid #1a1a4e}
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}
.player-card{background:#14142e;border:1px solid #2a2a4e;border-radius:10px;padding:12px;transition:all .2s}
.player-card:hover{border-color:#00d2ff;transform:translateY(-2px)}
.player-card .name{color:#fff;font-weight:bold;font-size:15px}
.player-card .team{color:#888;font-size:12px;margin-bottom:6px}
.player-card .stats{display:flex;flex-wrap:wrap;gap:4px 10px;font-size:12px}
.player-card .stats span{background:#1a1a3e;padding:2px 8px;border-radius:6px;white-space:nowrap}
.player-card .stats .hl{color:#ffd700}
table{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}
th{background:#14142e;color:#00d2ff;padding:8px 10px;text-align:left;font-size:12px;position:sticky;top:0;z-index:1}
td{padding:6px 10px;border-bottom:1px solid #1a1a4e}
tr:hover td{background:#1a1a3e}
.team-table td:first-child,.team-table th:first-child{width:40px;text-align:center}
.footer{text-align:center;color:#444;padding:30px 16px;font-size:12px}
.chart-wrap{background:#14142e;border:1px solid #2a2a4e;border-radius:10px;padding:12px;margin-bottom:16px}
.bar{height:6px;background:#1a1a4e;border-radius:3px;margin-top:4px}
.bar-fill{height:100%;border-radius:3px;background:linear-gradient(90deg,#00d2ff,#00ff88)}
@media(max-width:600px){.card-grid{grid-template-columns:1fr}.tabs{gap:4px}.tab-btn{padding:6px 14px;font-size:12px}}
</style>
</head>
<body>
<div class="header">
  <h1>ALGS Y6 Split1 Playoffs</h1>
  <p>Player Stats &middot; Team Rankings &middot; Interactive Data</p>
</div>
<div class="tabs" id="tabs"></div>
<div class="content" id="content"></div>
<div class="footer">Data: apexlegendsstatus.com &middot; Generated by ALGS Report Tool</div>

<script>
var DATA = ''' + json_str + ''';

var currentTab = null;

function renderTabs() {
  var tabs = document.getElementById("tabs");
  var content = document.getElementById("content");
  var keys = Object.keys(DATA);
  
  keys.forEach(function(g) {
    var btn = document.createElement("button");
    btn.className = "tab-btn";
    btn.textContent = DATA[g].label;
    btn.onclick = function() { switchTab(g); };
    tabs.appendChild(btn);
    
    var panel = document.createElement("div");
    panel.className = "tab-panel";
    panel.id = "panel-" + g;
    content.appendChild(panel);
  });
  
  if (keys.length > 0) switchTab(keys[0]);
}

function switchTab(g) {
  currentTab = g;
  document.querySelectorAll(".tab-btn").forEach(function(b, i) {
    b.classList.toggle("active", b.textContent === DATA[g].label);
  });
  document.querySelectorAll(".tab-panel").forEach(function(p) {
    p.classList.toggle("active", p.id === "panel-" + g);
  });
  renderPanel(g);
}

function renderPanel(g) {
  var d = DATA[g];
  var panel = document.getElementById("panel-" + g);
  
  var html = "";
  
  // Stats bar
  html += '<div class="stats-bar">';
  html += '<div class="stat-box"><div class="num">' + d.player_count + '</div><div class="lbl">Players</div></div>';
  html += '<div class="stat-box"><div class="num">' + d.team_count + '</div><div class="lbl">Teams</div></div>';
  html += '<div class="stat-box"><div class="num">' + d.groups.join(" vs ") + '</div><div class="lbl">Groups</div></div>';
  html += '</div>';

  // Top 5 Kills
  html += '<div class="section-title">Top 5 Kills</div>';
  html += '<div class="card-grid">';
  d.top_kills.forEach(function(p, i) {
    html += '<div class="player-card">';
    html += '<div class="name">#' + (i+1) + ' ' + p.name + '</div>';
    html += '<div class="team">' + p.team + '</div>';
    html += '<div class="stats">';
    html += '<span class="hl">Kills: ' + p.kills + '</span>';
    html += '<span>Dmg: ' + p.dmg + '</span>';
    html += '<span>K/D: ' + p.kd + '</span>';
    html += '<span>KA/D: ' + p.kad + '</span>';
    html += '</div></div>';
  });
  html += '</div>';

  // Top 5 Damage
  html += '<div class="section-title">Top 5 Damage</div>';
  html += '<div class="card-grid">';
  d.top_dmg.forEach(function(p, i) {
    html += '<div class="player-card">';
    html += '<div class="name">#' + (i+1) + ' ' + p.name + '</div>';
    html += '<div class="team">' + p.team + '</div>';
    html += '<div class="stats">';
    html += '<span class="hl">Dmg: ' + p.dmg + '</span>';
    html += '<span>Kills: ' + p.kills + '</span>';
    html += '<span>K/D: ' + p.kd + '</span>';
    html += '</div></div>';
  });
  html += '</div>';

  // Team Rankings
  html += '<div class="section-title">Team Rankings (by Kills)</div>';
  html += '<div style="max-height:400px;overflow-y:auto">';
  html += '<table class="team-table"><thead><tr><th>#</th><th>Team</th><th>Group</th><th>Kills</th><th>Damage</th><th></th></tr></thead><tbody>';
  var maxK = d.teams[0] ? d.teams[0].kills : 1;
  var maxD = d.teams[0] ? d.teams[0].dmg : 1;
  d.teams.forEach(function(t, i) {
    html += '<tr>';
    html += '<td>' + (i+1) + '</td>';
    html += '<td><strong>' + t.name + '</strong></td>';
    html += '<td>' + t.group + '</td>';
    html += '<td>' + t.kills + '</td>';
    html += '<td>' + t.dmg.toLocaleString() + '</td>';
    html += '<td style="width:120px"><div class="bar"><div class="bar-fill" style="width:' + (t.kills/maxK*100) + '%"></div></div></td>';
    html += '</tr>';
  });
  html += '</tbody></table></div>';

  // Full Player Table
  html += '<div class="section-title">All Players (by Damage)</div>';
  html += '<div style="max-height:500px;overflow-y:auto">';
  html += '<table><thead><tr><th>#</th><th>Player</th><th>Team</th><th>G</th><th>K</th><th>A</th><th>Dmg</th><th>K/D</th><th>KA/D</th><th>KP%</th></tr></thead><tbody>';
  d.players.forEach(function(p, i) {
    html += '<tr>';
    html += '<td>' + (i+1) + '</td>';
    html += '<td><strong>' + p.name + '</strong></td>';
    html += '<td>' + p.team + '</td>';
    html += '<td>' + p.games + '</td>';
    html += '<td>' + p.kills + '</td>';
    html += '<td>' + p.assists + '</td>';
    html += '<td>' + p.dmg + '</td>';
    html += '<td>' + p.kd + '</td>';
    html += '<td>' + p.kad + '</td>';
    html += '<td>' + p.kp + '%</td>';
    html += '</tr>';
  });
  html += '</tbody></table></div>';
  
  panel.innerHTML = html;
}

renderTabs();
</script>
</body>
</html>'''

# ====== 3. 输出 ======
output_path = os.path.join(PUBLIC_DIR, "index.html")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)

size_kb = os.path.getsize(output_path) / 1024
print(f"Built: {output_path} ({size_kb:.0f} KB)")
print(f"Open file:///{output_path} to preview")
print(f"Push to GitHub, enable Pages from /public folder")
