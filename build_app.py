#!/usr/bin/env python3
"""
ALGS 数据网站构建器 v3
- 雷达图/照片保存为独立文件，HTML 仅 ~50KB
- Team/Player 视图切换
- List/Radar 子视图
- 弹窗详情含照片
"""
import os, csv, json, re, io, sys, shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PUBLIC_DIR = os.path.join(BASE_DIR, "docs")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
THUMBS_DIR = os.path.join(PUBLIC_DIR, "thumbs")
PHOTOS_DIR = os.path.join(PUBLIC_DIR, "photos")
os.makedirs(THUMBS_DIR, exist_ok=True)
os.makedirs(PHOTOS_DIR, exist_ok=True)

sys.path.insert(0, SCRIPTS_DIR)
from team_utils import find_player_photo, get_team_abbr
from PIL import Image

GROUPS = {"ab": "Day1 A vs B", "ac": "Day2 A vs C", "bd": "Day2 B vs D", "bc": "Day3 B vs C", "ad": "Day3 A vs D", "cd": "Day1 C vs D"}

all_data = {}
for g, label in GROUPS.items():
    csv_path = os.path.join(DATA_DIR, g, "algs_players_data.csv")
    radar_dir = os.path.join(DATA_DIR, g, "radar_charts")
    if not os.path.exists(csv_path):
        continue

    rows = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows.append(r)

    teams = {}
    for r in rows:
        t = r["Team"]
        if t not in teams:
            teams[t] = {"k": 0, "d": 0, "g": r.get("Group", "")}
        teams[t]["k"] += int(r.get("Kills", "0") or "0")
        teams[t]["d"] += int(r.get("DmgDealt", "0") or "0")

    players = []
    for p in sorted(rows, key=lambda x: int(x.get("DmgDealt", "0") or "0"), reverse=True):
        name = p["Player"]
        team = p["Team"]
        pid = f"{g}_{re.sub(r'[^a-zA-Z0-9_-]', '_', name)}"
        name_slug = re.sub(r'[\\/:*?"<>| ]', '_', name)
        name_slug = re.sub(r'[^a-zA-Z0-9_-]', '_', name_slug)
        radar_src = os.path.join(radar_dir, f"{name_slug}.png")

        # Save radar thumbnail
        thumb_file = f"{pid}.jpg"
        thumb_path = os.path.join(THUMBS_DIR, thumb_file)
        has_radar = False
        if os.path.exists(radar_src) and not os.path.exists(thumb_path):
            try:
                img = Image.open(radar_src).convert("RGB")
                img.thumbnail((200, 200), Image.LANCZOS)
                img.save(thumb_path, "JPEG", quality=60)
            except:
                pass
        if os.path.exists(thumb_path):
            has_radar = True

        # Save photo thumbnail
        photo_file = f"{pid}_photo.jpg"
        photo_path = os.path.join(PHOTOS_DIR, photo_file)
        has_photo = False
        ppath, abbr = find_player_photo(name, team_name=team)
        if ppath and not os.path.exists(photo_path):
            try:
                img = Image.open(ppath).convert("RGB")
                img.thumbnail((120, 120), Image.LANCZOS)
                img.save(photo_path, "JPEG", quality=50)
            except:
                pass
        if os.path.exists(photo_path):
            has_photo = True

        players.append({
            "name": name, "team": team, "group": p.get("Group", ""),
            "kills": p.get("Kills", "0"), "assists": p.get("Assists", "0"),
            "dmg": p.get("DmgDealt", "0"), "kd": p.get("KD", "0"),
            "kad": p.get("KAD", "0"), "kp": p.get("KillParticipationPct", "0"),
            "bestp": p.get("BestP", ""), "games": p.get("Games", "0"),
            "thumb": f"thumbs/{thumb_file}" if has_radar else None,
            "photo": f"photos/{photo_file}" if has_photo else None,
        })

    all_data[g] = {
        "label": label,
        "player_count": len(rows), "team_count": len(teams),
        "groups": sorted(set(r.get("Group", "") for r in rows)),
        "teams": [
            {"name": t, "kills": td["k"], "dmg": td["d"], "group": td["g"]}
            for t, td in sorted(teams.items(), key=lambda x: x[1]["k"], reverse=True)
        ],
        "players": players,
    }
    print(f"{g}: {len(rows)} players, {sum(1 for p in players if p['thumb'])} radars, {sum(1 for p in players if p['photo'])} photos")

json_str = json.dumps(all_data, ensure_ascii=False)

# ====== HTML ======
html = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta http-equiv="Cache-Control" content="no-cache, must-revalidate"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ALGS Y6 Split1 Playoffs — Data Report v648256</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,'Segoe UI',Arial,sans-serif;background:#0a0a1a;color:#ccc}
.header{background:linear-gradient(135deg,#0f0f2e,#1a1040);padding:20px;text-align:center;border-bottom:2px solid #1a1a4e}
.header h1{color:#00d2ff;font-size:clamp(18px,4vw,26px)}
.header p{color:#888;font-size:13px;margin-top:4px}
.tabs{display:flex;justify-content:center;gap:6px;padding:14px 8px;flex-wrap:wrap}
.tab-btn,.view-btn{background:#14142e;color:#888;border:1px solid #2a2a4e;padding:7px 16px;border-radius:18px;cursor:pointer;font-size:13px;transition:.2s}
.tab-btn:hover,.view-btn:hover{color:#00d2ff;border-color:#00d2ff}
.tab-btn.active,.view-btn.active{background:#00d2ff;color:#0a0a1a;border-color:#00d2ff;font-weight:bold}
.view-bar{display:flex;justify-content:center;gap:8px;padding:0 16px 10px;flex-wrap:wrap}
.sub-bar{display:flex;justify-content:center;gap:6px;padding:0 16px 8px}
.content{max-width:1200px;margin:0 auto;padding:0 12px 40px}
.tab-panel{display:none}.tab-panel.active{display:block}
.view-panel{display:none}.view-panel.active{display:block}
.stats-bar{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}
.stat-box{background:#14142e;border:1px solid #2a2a4e;border-radius:10px;padding:10px 14px;flex:1;min-width:100px;text-align:center}
.stat-box .num{color:#00d2ff;font-size:22px;font-weight:bold}
.stat-box .lbl{color:#666;font-size:11px;margin-top:2px}
.table-wrap{max-height:500px;overflow-y:auto;border:1px solid #1a1a4e;border-radius:8px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#14142e;color:#00d2ff;padding:7px 8px;text-align:left;font-size:11px;position:sticky;top:0;z-index:1}
td{padding:5px 8px;border-bottom:1px solid #1a1a4e}
tr:hover td{background:#1a1a3e}
.bar-wrap{width:80px;height:5px;background:#1a1a4e;border-radius:3px;display:inline-block;vertical-align:middle;margin-left:6px}
.bar-fill{height:100%;border-radius:3px;background:linear-gradient(90deg,#00d2ff,#00ff88)}
.radar-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px}
.radar-card{background:#14142e;border:1px solid #2a2a4e;border-radius:10px;padding:8px;text-align:center;cursor:pointer;transition:.2s}
.radar-card:hover{border-color:#00d2ff;transform:translateY(-2px)}
.radar-card img{width:100%;border-radius:6px;display:block;background:#0a0a1a}
.radar-card .rname{color:#fff;font-size:13px;margin-top:4px;font-weight:bold}
.radar-card .rteam{color:#888;font-size:11px}
.modal-overlay{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);z-index:1000;justify-content:center;align-items:center}
.modal-overlay.active{display:flex}
.modal-box{background:#1a1a2e;border:2px solid #00d2ff;border-radius:16px;padding:24px;max-width:700px;width:95%;max-height:90vh;overflow-y:auto;position:relative;animation:fadeIn .25s}
@keyframes fadeIn{from{opacity:0;transform:scale(.95)}to{opacity:1;transform:scale(1)}}
.modal-close{position:absolute;top:10px;right:16px;background:none;border:none;color:#888;font-size:26px;cursor:pointer}
.modal-close:hover{color:#fff}
.modal-header{display:flex;gap:16px;flex-wrap:wrap;align-items:flex-start;margin-bottom:16px}
.modal-radar{width:260px;border-radius:10px;flex-shrink:0}
.modal-photo{width:80px;height:80px;border-radius:50%;object-fit:cover;border:3px solid #00d2ff;flex-shrink:0}
.modal-title h2{color:#00d2ff;font-size:20px;margin-bottom:4px}
.modal-title .team{color:#888;font-size:13px;margin-bottom:8px}
.modal-stats{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px}
.modal-stat{background:#16213e;border-radius:8px;padding:10px 12px}
.modal-stat .label{color:#888;font-size:10px;text-transform:uppercase}
.modal-stat .value{color:#fff;font-size:18px;font-weight:bold;margin-top:2px}
.modal-stat .value.hl{color:#00d2ff}
.player-row{cursor:pointer}.player-row:hover{background:#1a1a3e!important}
@media(max-width:600px){.radar-grid{grid-template-columns:repeat(2,1fr)}.modal-radar{width:100%}}
</style>
</head>
<body>
<div class="header"><h1>ALGS Y6 Split1 Playoffs</h1><p>Player Stats · Team Rankings · Radar Charts</p></div>
<div class="tabs" id="tabs"></div>
<div class="content" id="content"></div>
<div class="modal-overlay" id="modal" onclick="if(event.target===this)hideModal()">
<div class="modal-box" onclick="event.stopPropagation()">
<button class="modal-close" onclick="hideModal()">&times;</button>
<div id="modal-content"></div></div></div>
<script>
var DATA = ''' + json_str + r''';
var currentView = "teams";
var playerMode = "list";

(function init(){
  var tabs=document.getElementById("tabs"), content=document.getElementById("content");
  Object.keys(DATA).forEach(function(g){
    var btn=document.createElement("button");btn.className="tab-btn";btn.textContent=DATA[g].label;
    btn.onclick=function(){switchGroup(g);};tabs.appendChild(btn);
    var p=document.createElement("div");p.className="tab-panel";p.id="panel-"+g;content.appendChild(p);
  });
  if(Object.keys(DATA).length)switchGroup(Object.keys(DATA)[0]);
})();

function switchGroup(g){
  document.querySelectorAll(".tab-btn").forEach(function(b){b.classList.toggle("active",b.textContent===DATA[g].label)});
  document.querySelectorAll(".tab-panel").forEach(function(p){p.classList.toggle("active",p.id==="panel-"+g)});
  renderPanel(g);
}

function renderPanel(g){
  var d=DATA[g], panel=document.getElementById("panel-"+g), h="";
  h+='<div class="stats-bar">';
  h+='<div class="stat-box"><div class="num">'+d.player_count+'</div><div class="lbl">Players</div></div>';
  h+='<div class="stat-box"><div class="num">'+d.team_count+'</div><div class="lbl">Teams</div></div>';
  h+='<div class="stat-box"><div class="num">'+d.groups.join(" vs ")+'</div><div class="lbl">Groups</div></div></div>';
  h+='<div class="view-bar">';
  h+='<button class="view-btn'+(currentView==="teams"?" active":"")+'" onclick="switchView(\'teams\',\''+g+'\')">Team Data</button>';
  h+='<button class="view-btn'+(currentView==="players"?" active":"")+'" onclick="switchView(\'players\',\''+g+'\')">Player Data</button></div>';
  
  // Teams
  h+='<div class="view-panel'+(currentView==="teams"?" active":"")+'" id="view-teams-'+g+'"><div class="table-wrap"><table><thead><tr><th>#</th><th>Team</th><th>G</th><th>Kills</th><th>Damage</th><th></th></tr></thead><tbody>';
  var mk=d.teams[0]?d.teams[0].kills:1;
  d.teams.forEach(function(t,i){h+='<tr><td>'+(i+1)+'</td><td><strong>'+t.name+'</strong></td><td>'+t.group+'</td><td>'+t.kills+'</td><td>'+t.dmg.toLocaleString()+'</td><td><span class="bar-wrap"><span class="bar-fill" style="width:'+(t.kills/mk*100)+'%"></span></span></td></tr>';});
  h+='</tbody></table></div></div>';

  // Players
  h+='<div class="view-panel'+(currentView==="players"?" active":"")+'" id="view-players-'+g+'">';
  h+='<div class="sub-bar">';
  h+='<button class="view-btn'+(playerMode==="list"?" active":"")+'" onclick="switchPlayerMode(\'list\',\''+g+'\')">List</button>';
  h+='<button class="view-btn'+(playerMode==="radar"?" active":"")+'" onclick="switchPlayerMode(\'radar\',\''+g+'\')">Radar Charts</button></div>';
  
  // List
  h+='<div class="view-panel'+(playerMode==="list"?" active":"")+'" id="pmode-list-'+g+'"><div class="table-wrap"><table><thead><tr><th>#</th><th>Player</th><th>Team</th><th>K</th><th>A</th><th>Dmg</th><th>K/D</th><th>KA/D</th><th>KP%</th></tr></thead><tbody>';
  d.players.forEach(function(p,i){h+='<tr class="player-row" onclick="showDetail(\''+g+'\','+i+')"><td>'+(i+1)+'</td><td><strong>'+p.name+'</strong></td><td>'+p.team+'</td><td>'+p.kills+'</td><td>'+p.assists+'</td><td>'+p.dmg+'</td><td>'+p.kd+'</td><td>'+p.kad+'</td><td>'+p.kp+'%</td></tr>';});
  h+='</tbody></table></div></div>';

  // Radar grid
  h+='<div class="view-panel'+(playerMode==="radar"?" active":"")+'" id="pmode-radar-'+g+'"><div class="radar-grid">';
  d.players.forEach(function(p,i){if(p.thumb)h+='<div class="radar-card" onclick="showDetail(\''+g+'\','+i+')"><img src="'+p.thumb+'" alt="'+p.name+'" loading="lazy"><div class="rname">'+p.name+'</div><div class="rteam">'+p.team+'</div></div>';});
  h+='</div></div></div>';

  panel.innerHTML=h;

}

function showDetail(g,idx){
  var p=DATA[g].players[idx], h='<div class="modal-header">';
  if(p.thumb)h+='<img class="modal-radar" src="'+p.thumb+'">';
  if(p.photo)h+='<img class="modal-photo" src="'+p.photo+'">';
  h+='<div class="modal-title"><h2>'+p.name+'</h2><div class="team">'+p.team+' | G'+p.group+' | Best: '+p.bestp+'</div></div></div>';
  h+='<div class="modal-stats">';
  [["Kills",p.kills,1],["Assists",p.assists,1],["Damage",p.dmg,1],["K/D",p.kd,1],["KA/D",p.kad,1],["KP%",p.kp+"%",0],["Games",p.games,0],["Best",p.bestp,0]].forEach(function(s){h+='<div class="modal-stat"><div class="label">'+s[0]+'</div><div class="value'+(s[2]?' hl':'')+'">'+s[1]+'</div></div>';});
  h+='</div>';
  document.getElementById("modal-content").innerHTML=h;
  document.getElementById("modal").classList.add("active");
}
function hideModal(){document.getElementById("modal").classList.remove("active");}
document.addEventListener("keydown",function(e){if(e.key==="Escape")hideModal();});

function switchView(v,g){currentView=v;renderPanel(g);}
function switchPlayerMode(m,g){playerMode=m;renderPanel(g);}
</script>
</body>
</html>'''

output_path = os.path.join(PUBLIC_DIR, "index.html")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)
html_kb = os.path.getsize(output_path) / 1024
print(f"\nHTML: {html_kb:.0f} KB")
print(f"Thumbs: {len(os.listdir(THUMBS_DIR))} files")
print(f"Photos: {len(os.listdir(PHOTOS_DIR))} files")
print(f"Output: {output_path}")
