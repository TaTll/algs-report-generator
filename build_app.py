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

GROUPS = {"ab": "Day1 A vs B", "ac": "Day2 A vs C", "bd": "Day2 B vs D", "bc": "Day3 B vs C", "ad": "Day3 A vs D", "cd": "Day1 C vs D", "sf": "Survivor Stage"}



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




# ====== All Players (aggregated across all groups) ======
from collections import defaultdict as _dd
_ap = _dd(lambda: {"team": "", "group": set(), "kills": 0, "assists": 0, "dmg": 0, "games": 0, "match_count": 0, "kd_sum": 0, "kad_sum": 0, "kp_sum": 0})
for _g in GROUPS:
    _path = os.path.join(DATA_DIR, _g, "algs_players_data.csv")
    if not os.path.exists(_path): continue
    with open(_path, "r", encoding="utf-8-sig") as _f:
        for _r in csv.DictReader(_f):
            _n = _r["Player"]; _ap[_n]["team"] = _r.get("Team", ""); _ap[_n]["group"].add(_r.get("Group", ""))
            _ap[_n]["kills"] += int(_r.get("Kills", "0") or "0"); _ap[_n]["assists"] += int(_r.get("Assists", "0") or "0")
            _ap[_n]["dmg"] += int(_r.get("DmgDealt", "0") or "0"); _ap[_n]["games"] += int(_r.get("Games", "0") or "0")
            _ap[_n]["match_count"] += 1
            try: _ap[_n]["kd_sum"] += float(_r.get("KD", "0") or "0")
            except: pass
            try: _ap[_n]["kad_sum"] += float(_r.get("KAD", "0") or "0")
            except: pass
            try: _ap[_n]["kp_sum"] += float(_r.get("KillParticipationPct", "0") or "0")
            except: pass
_all_teams = _dd(lambda: {"kills": 0, "dmg": 0})
_all_plist = []
for _n, _d in _ap.items():
    _mc = _d["match_count"]; _all_teams[_d["team"]]["kills"] += _d["kills"]; _all_teams[_d["team"]]["dmg"] += _d["dmg"]
    _all_plist.append({"name": _n, "team": _d["team"], "groups": sorted(_d["group"]), "kills": _d["kills"], "assists": _d["assists"], "dmg": _d["dmg"], "games": _d["games"], "matches": _mc, "avg_kd": round(_d["kd_sum"]/_mc,2) if _mc else 0, "avg_kad": round(_d["kad_sum"]/_mc,2) if _mc else 0, "avg_kp": round(_d["kp_sum"]/_mc,1) if _mc else 0})
_all_plist.sort(key=lambda x: x["dmg"], reverse=True)
_all_tlist = [{"name": _t, "kills": _td["kills"], "dmg": _td["dmg"]} for _t, _td in sorted(_all_teams.items(), key=lambda x: x[1]["kills"], reverse=True)]
all_data["all"] = {"label": "All Players", "player_count": len(_all_plist), "team_count": len(_all_teams), "groups": ["All"], "teams": _all_tlist, "players": _all_plist}
# ====== Overall Standings ======
all_data["overall"] = {
    "label": "Overall Standings",
    "player_count": 40, "team_count": 40, "groups": ["All"], "teams": [], "players": [],
    "standings": [{"rank":1,"team":"ELITE Esports","group":"C","score":199,"status":"Finals"},
        {"rank":2,"team":"Team Liquid","group":"D","score":182,"status":"Finals"},
        {"rank":3,"team":"S8UL","group":"D","score":161,"status":"Finals"},
        {"rank":4,"team":"Team Vision","group":"D","score":139,"status":"Finals"},
        {"rank":5,"team":"GaiminGladiators","group":"A","score":139,"status":"Finals"},
        {"rank":6,"team":"ZETA DIVISION","group":"A","score":137,"status":"Finals"},
        {"rank":7,"team":"AG GLOBAL","group":"A","score":134,"status":"Finals"},
        {"rank":8,"team":"REJECT","group":"C","score":128,"status":"Finals"},
        {"rank":9,"team":"ZEDI ESPORTS","group":"A","score":127,"status":"Finals"},
        {"rank":10,"team":"Team Falcons","group":"B","score":120,"status":"Finals"},
        {"rank":11,"team":"Team Nemesis","group":"C","score":116,"status":"Finals"},
        {"rank":12,"team":"Sentinels","group":"C","score":116,"status":"Finals"},
        {"rank":13,"team":"Alliance","group":"C","score":108,"status":"Finals"},
        {"rank":14,"team":"UNLIMIT","group":"B","score":106,"status":"Finals"},
        {"rank":15,"team":"Virtus.pro","group":"B","score":106,"status":"Survivor"},
        {"rank":16,"team":"Wolves Esports","group":"B","score":105,"status":"Survivor"},
        {"rank":17,"team":"Team RRQ","group":"C","score":104,"status":"Survivor"},
        {"rank":18,"team":"NinjasinPyjamas","group":"C","score":104,"status":"Survivor"},
        {"rank":19,"team":"VK GAMING","group":"C","score":102,"status":"Survivor"},
        {"rank":20,"team":"ForFun Esports","group":"A","score":101,"status":"Survivor"},
        {"rank":21,"team":"ShopifyRebellion","group":"B","score":101,"status":"Survivor"},
        {"rank":22,"team":"KINOTROPE CLUB","group":"C","score":101,"status":"Survivor"},
        {"rank":23,"team":"DINOS","group":"D","score":99,"status":"Survivor"},
        {"rank":24,"team":"JD GAMING","group":"A","score":97,"status":"Survivor"},
        {"rank":25,"team":"ZIPLINE MAFIA","group":"D","score":92,"status":"Survivor"},
        {"rank":26,"team":"PXX","group":"A","score":90,"status":"Survivor"},
        {"rank":27,"team":"Geekay Esports","group":"C","score":84,"status":"Survivor"},
        {"rank":28,"team":"FLAT","group":"B","score":83,"status":"Survivor"},
        {"rank":29,"team":"ENTER FORCE.36","group":"D","score":81,"status":"Survivor"},
        {"rank":30,"team":"TIE","group":"A","score":80,"status":"Survivor"},
        {"rank":31,"team":"WGR NEO","group":"D","score":74,"status":"Survivor"},
        {"rank":32,"team":"GenG Esports","group":"B","score":74,"status":"Survivor"},
        {"rank":33,"team":"AURORA","group":"D","score":70,"status":"Survivor"},
        {"rank":34,"team":"Relove DCG","group":"A","score":70,"status":"Survivor"},
        {"rank":35,"team":"Kirisame Havoc","group":"B","score":67,"status":"Eliminated"},
        {"rank":36,"team":"TEAM HERETICS","group":"B","score":66,"status":"Eliminated"},
        {"rank":37,"team":"Dogred","group":"D","score":66,"status":"Eliminated"},
        {"rank":38,"team":"TLN Pirates","group":"D","score":61,"status":"Eliminated"},
        {"rank":39,"team":"Dory","group":"B","score":43,"status":"Eliminated"},
        {"rank":40,"team":"TriniTY","group":"A","score":31,"status":"Eliminated"},
    ],
}
json_str = json.dumps(all_data, ensure_ascii=False)

# ====== HTML ======
html = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta http-equiv="Cache-Control" content="no-cache, must-revalidate"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ALGS Y6 Split1 Playoffs — Data Report v648256</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#14161a;color:#c8ccd4;line-height:1.5}
.header{background:#1a1d23;border-bottom:1px solid #2a2d33;padding:16px 20px}
.header h1{color:#e0e2e6;font-size:18px;font-weight:600;letter-spacing:-0.3px}
.header p{color:#7a7f87;font-size:12px;margin-top:2px}
.tabs{display:flex;gap:0;padding:0 20px;background:#1a1d23;border-bottom:1px solid #2a2d33;flex-wrap:wrap}
.tab-btn{background:none;color:#7a7f87;border:none;padding:10px 16px;cursor:pointer;font-size:13px;border-bottom:2px solid transparent;transition:.15s;white-space:nowrap}
.tab-btn:hover{color:#c8ccd4}
.tab-btn.active{color:#e0e2e6;border-bottom-color:#c8942e}
.subtabs{display:flex;gap:2px;padding:6px 20px;background:#111316;border-bottom:1px solid #2a2d33;flex-wrap:wrap}
.subtabs .tab-btn{font-size:11px;padding:5px 12px;border-bottom:none;border-radius:3px;border:1px solid transparent}.subtabs .tab-btn.active{background:#1a1d23;border-color:#2a2d33;color:#e0e2e6;border-bottom:none}
.content{max-width:1100px;margin:0 auto;padding:20px}
.tab-panel{display:none}.tab-panel.active{display:block}
.view-panel{display:none}.view-panel.active{display:block}
.stats-bar{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}
.stat-box{background:#1a1d23;border:1px solid #2a2d33;border-radius:4px;padding:14px 18px;flex:1;min-width:100px;text-align:center}
.stat-box .num{color:#e0e2e6;font-size:24px;font-weight:600}
.stat-box .lbl{color:#7a7f87;font-size:11px;margin-top:2px;text-transform:uppercase;letter-spacing:0.5px}
.sec-title{color:#e0e2e6;font-size:16px;font-weight:600;margin-bottom:12px}
.view-bar{display:flex;gap:4px;margin-bottom:14px}
.view-btn{background:#1a1d23;color:#7a7f87;border:1px solid #2a2d33;padding:6px 14px;border-radius:3px;cursor:pointer;font-size:12px}
.view-btn:hover{color:#c8ccd4;border-color:#3a3d43}
.view-btn.active{background:#2a2d33;color:#e0e2e6;border-color:#3a3d43}
.table-wrap{border:1px solid #2a2d33;border-radius:4px;overflow:hidden;margin-bottom:16px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#1a1d23;color:#9a9ea6;padding:8px 10px;text-align:left;font-size:11px;font-weight:500;text-transform:uppercase;letter-spacing:0.3px;border-bottom:1px solid #2a2d33}
td{padding:7px 10px;border-bottom:1px solid #1f2128;color:#c8ccd4}
tr:hover td{background:rgba(255,255,255,0.02)}
tr:nth-child(even) td{background:rgba(255,255,255,0.01)}
tr:nth-child(even):hover td{background:rgba(255,255,255,0.03)}
.radar-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px}
.radar-card{background:#1a1d23;border:1px solid #2a2d33;border-radius:4px;padding:8px;text-align:center;cursor:pointer;transition:.15s}
.radar-card:hover{border-color:#3a3d43;background:#1f2128}
.radar-card img{width:100%;border-radius:2px;display:block}
.radar-card .rname{color:#e0e2e6;font-size:12px;margin-top:6px;font-weight:500}
.radar-card .rteam{color:#7a7f87;font-size:11px}
.modal-overlay{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);z-index:1000;justify-content:center;align-items:center}
.modal-overlay.active{display:flex}
.modal-box{background:#1a1d23;border:1px solid #2a2d33;border-radius:8px;padding:24px;max-width:640px;width:95%;max-height:90vh;overflow-y:auto;position:relative;animation:fadeIn .2s}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.modal-close{position:absolute;top:10px;right:14px;background:none;border:none;color:#7a7f87;font-size:22px;cursor:pointer}
.modal-close:hover{color:#e0e2e6}
.modal-header{display:flex;gap:16px;flex-wrap:wrap;align-items:flex-start;margin-bottom:18px}
.modal-radar{width:240px;border-radius:4px;flex-shrink:0}
.modal-photo{width:72px;height:72px;border-radius:50%;object-fit:cover;border:2px solid #2a2d33;flex-shrink:0}
.modal-title h2{color:#e0e2e6;font-size:18px;font-weight:600;margin-bottom:2px}
.modal-title .team{color:#7a7f87;font-size:12px}
.modal-stats{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px}
.modal-stat{background:rgba(255,255,255,0.03);border:1px solid #2a2d33;border-radius:4px;padding:10px 12px}
.modal-stat .label{color:#7a7f87;font-size:10px;text-transform:uppercase;letter-spacing:0.5px}
.modal-stat .value{color:#e0e2e6;font-size:17px;font-weight:600;margin-top:2px}
.modal-stat .value.hl{color:#c8942e}
.player-row{cursor:pointer}
th.sortable{cursor:pointer;user-select:none;position:relative}
th.sortable:hover{color:#c8942e}
th.sortable .arrow{display:inline-block;margin-left:4px;opacity:0;font-size:10px;transition:.15s}
th.sortable:hover .arrow{opacity:0.4}
th.sortable.asc .arrow,th.sortable.desc .arrow{opacity:1;color:#c8942e}
th.sortable.asc .arrow::after{content:' ▲'}
th.sortable.desc .arrow::after{content:' ▼'}
@media(max-width:600px){.radar-grid{grid-template-columns:repeat(2,1fr)}.modal-radar{width:100%}.tabs{padding:0 8px}.tab-btn{padding:8px 10px;font-size:12px}}
</style>
</head>
<body>
<div class="header"><h1>ALGS Y6 Split1 Playoffs</h1><p>Player Stats · Team Rankings · Radar Charts</p></div>
<div class="tabs" id="tabs"></div>
<div class="subtabs" id="subtabs" style="display:none"></div>
<div class="content" id="content"></div>
<div class="modal-overlay" id="modal" onclick="if(event.target===this)hideModal()">
<div class="modal-box" onclick="event.stopPropagation()">
<button class="modal-close" onclick="hideModal()">&times;</button>
<div id="modal-content"></div></div></div>
<script>
var DATA = __JSON_PLACEHOLDER__;
var playerMode = "list";
var GROUPS = ["ab","ac","ad","bc","bd","cd"];
var GROUP_LABELS = {"ab":"Day1 A vs B","ac":"Day2 A vs C","ad":"Day3 A vs D","bc":"Day3 B vs C","bd":"Day2 B vs D","cd":"Day1 C vs D"};

(function init(){
  var tabs=document.getElementById("tabs"), subtabs=document.getElementById("subtabs"), content=document.getElementById("content");
  addTab("overall","Overall Standings");
  addTab("all","All Players");
  addTab("group","Group Stage");
  addTab("sf","Survivor Stage");
  GROUPS.forEach(function(g){
    var b=document.createElement("button");b.className="tab-btn sub-item";b.textContent=GROUP_LABELS[g];
    b.onclick=function(){switchGroup(g);};
    subtabs.appendChild(b);
  });
  ["overall","all","sf"].concat(GROUPS).forEach(function(g){
    var p=document.createElement("div");p.className="tab-panel";p.id="panel-"+g;content.appendChild(p);
  });
  switchGroup("overall");
})();

function addTab(g,label){
  var btn=document.createElement("button");btn.className="tab-btn";btn.textContent=label;
  btn.onclick=function(){switchGroup(g);};
  document.getElementById("tabs").appendChild(btn);
}

function switchGroup(g){
  var isGroup=GROUPS.indexOf(g)>=0;
  var subtabs=document.getElementById("subtabs");
  if(g==="group"){subtabs.style.display="flex";switchGroup(GROUPS[0]);return;}
  subtabs.style.display=isGroup?"flex":"none";
  var topLabel=isGroup?"Group Stage":DATA[g].label;
  document.querySelector("#tabs").querySelectorAll(".tab-btn").forEach(function(b){b.classList.toggle("active",b.textContent===topLabel);});
  if(isGroup){document.querySelector("#subtabs").querySelectorAll(".tab-btn").forEach(function(b){b.classList.toggle("active",b.textContent===GROUP_LABELS[g]);});}
  document.querySelectorAll(".tab-panel").forEach(function(p){p.classList.toggle("active",p.id==="panel-"+g);});
  renderPanel(g);
}


function sortPlayers(g, col, th) {
  if (sortCol === col) { sortAsc = !sortAsc; } else { sortCol = col; sortAsc = true; }
  var d = DATA[g], players = d.players.slice();
  var getVal = function(p) {
    var v = p[col]; if (v === undefined || v === null) return 0;
    if (typeof v === 'string' && v.indexOf('%') > -1) return parseFloat(v);
    var n = parseFloat(v);
    return isNaN(n) ? (v || 0) : n;
  };
  players.sort(function(a, b) {
    var va = getVal(a), vb = getVal(b);
    if (typeof va === 'string') return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
    return sortAsc ? va - vb : vb - va;
  });
  // Update headers
  th.parentNode.querySelectorAll('th').forEach(function(h, i) {
    h.classList.remove('asc', 'desc');
    if (h.dataset.col === col) h.classList.add(sortAsc ? 'asc' : 'desc');
  });
  // Rebuild tbody
  var tbody = '', ph = g === "all" ? ["#","Player","Team","G","M","K","A","Dmg","K/D","KA/D","KP%"] : ["#","Player","Team","K","A","Dmg","K/D","KA/D","KP%"];
  var cols = g === "all" ? [null,"name","team","games","matches","kills","assists","dmg","avg_kd","avg_kad","avg_kp"] : [null,"name","team","kills","assists","dmg","kd","kad","kp"];
  players.forEach(function(p, i) {
    tbody += '<tr class="player-row" onclick="showDetail(' + JSON.stringify(g) + ',' + d.players.indexOf(p) + ')"><td>' + (i + 1) + '</td>';
    for (var ci = 1; ci < cols.length; ci++) {
      var val = cols[ci] ? (p[cols[ci]] || '') : '';
      tbody += '<td>' + (ci <= 2 ? '<strong>' + val + '</strong>' : val) + '</td>';
    }
    tbody += '</tr>';
  });
  th.closest('table').querySelector('tbody').innerHTML = tbody;
}
function renderPanel(g){
  var d = DATA[g], panel = document.getElementById("panel-" + g), h = "";

  if (g === "overall") {
    h += '<div class="stats-bar">';
    h += '<div class="stat-box"><div class="num">40</div><div class="lbl">Teams</div></div>';
    h += '<div class="stat-box"><div class="num" style="color:#00ff88">14</div><div class="lbl">Finals</div></div>';
    h += '<div class="stat-box"><div class="num" style="color:#ffd700">20</div><div class="lbl">Survivor</div></div>';
    h += '<div class="stat-box"><div class="num" style="color:#ff4444">6</div><div class="lbl">Eliminated</div></div></div>';
    h += '<div class="table-wrap"><table><thead><tr><th>#</th><th>Team</th><th>G</th><th>Score</th><th>Status</th></tr></thead><tbody>';
    d.standings.forEach(function(s){
      var c = s.status === "Finals" ? "#00ff88" : s.status === "Survivor" ? "#ffd700" : "#ff4444";
      h += '<tr><td>' + s.rank + '</td><td><strong>' + s.team + '</strong></td><td>G' + s.group + '</td><td><strong>' + s.score + '</strong></td><td style="color:' + c + '">' + s.status + '</td></tr>';
    });
    h += '</tbody></table></div>';
    panel.innerHTML = h;
    return;
  }

  h += '<div class="stats-bar">';
  h += '<div class="stat-box"><div class="num">' + d.player_count + '</div><div class="lbl">Players</div></div>';
  h += '<div class="stat-box"><div class="num">' + d.team_count + '</div><div class="lbl">Teams</div></div>';
  h += '<div class="stat-box"><div class="num">' + (d.groups ? d.groups.join(" vs ") : "All") + '</div><div class="lbl">Groups</div></div></div>';

  if (g === "all") {
    h += '<div class="table-wrap" style="max-height:250px;margin-bottom:12px"><table><thead><tr><th>#</th><th>Team</th><th>Kills</th><th>Damage</th></tr></thead><tbody>';
    var mk = d.teams[0] ? d.teams[0].kills : 1;
    d.teams.forEach(function(t, i) {
      h += '<tr><td>' + (i + 1) + '</td><td><strong>' + t.name + '</strong></td><td>' + t.kills + '</td><td>' + t.dmg.toLocaleString() + '</td></tr>';
    });
    h += '</tbody></table></div>';
  }

  h += '<div class="sub-bar">';
  h += '<button class="view-btn' + (playerMode === "list" ? " active" : "") + '" id="btn-list-' + g + '">List</button>';
  if (g !== "all") h += '<button class="view-btn' + (playerMode === "radar" ? " active" : "") + '" id="btn-radar-' + g + '">Radar Charts</button>';
  h += '</div>';

  // List view
  h += '<div class="view-panel' + (playerMode === "list" ? " active" : "") + '" id="pm-list-' + g + '">';
  var ph = g === "all" ? ["#", "Player", "Team", "G", "M", "K", "A", "Dmg", "KD", "KAD", "KP%"] : ["#", "Player", "Team", "K", "A", "Dmg", "K/D", "KA/D", "KP%"];
  h += '<div class="table-wrap"><table><thead><tr>';
  var cols = g === "all" ? [null,"name","team","games","matches","kills","assists","dmg","avg_kd","avg_kad","avg_kp"] : [null,"name","team","kills","assists","dmg","kd","kad","kp"];
  ph.forEach(function(x, i) { var sc = cols[i]; h += '<th' + (sc ? ' class="sortable" data-col="' + sc + '" onclick="sortPlayers(\'' + g + '\',\'' + sc + '\',this)"' : '') + '>' + x + '<span class="arrow"></span></th>'; });
  h += '</tr></thead><tbody>';
  d.players.forEach(function(p, i) {
    h += '<tr class="player-row" onclick="showDetail(' + JSON.stringify(g) + ',' + i + ')"><td>' + (i + 1) + '</td><td><strong>' + p.name + '</strong></td><td>' + p.team + '</td>';
    if (g === "all") { h += '<td>' + p.games + '</td><td>' + p.matches + '</td>'; }
    h += '<td>' + p.kills + '</td><td>' + p.assists + '</td><td>' + p.dmg + '</td><td>' + (g === "all" ? p.avg_kd : p.kd) + '</td><td>' + (g === "all" ? p.avg_kad : p.kad) + '</td><td>' + (g === "all" ? p.avg_kp : p.kp) + '%</td></tr>';
  });
  h += '</tbody></table></div></div>';

  // Radar view (group matches only)
  if (g !== "all") {
    h += '<div class="view-panel' + (playerMode === "radar" ? " active" : "") + '" id="pm-radar-' + g + '"><div class="radar-grid">';
    d.players.forEach(function(p, i) {
      if (p.thumb) h += '<div class="radar-card" onclick="showDetail(' + JSON.stringify(g) + ',' + i + ')"><img src="' + p.thumb + '" alt="' + p.name + '" loading="lazy"><div class="rname">' + p.name + '</div><div class="rteam">' + p.team + '</div></div>';
    });
    h += '</div></div>';
  }

  panel.innerHTML = h;
  // Re-bind buttons
  var bl = document.getElementById("btn-list-" + g);
  if (bl) bl.onclick = function() { playerMode = "list"; renderPanel(g); };
  var br = document.getElementById("btn-radar-" + g);
  if (br) br.onclick = function() { playerMode = "radar"; renderPanel(g); };
}

function showDetail(g, idx) {
  var p = DATA[g].players[idx], h = '<div class="modal-header">';
  if (p.thumb) h += '<img class="modal-radar" src="' + p.thumb + '">';
  if (p.photo) h += '<img class="modal-photo" src="' + p.photo + '">';
  h += '<div class="modal-title"><h2>' + p.name + '</h2><div class="team">' + p.team + '</div></div></div>';
  h += '<div class="modal-stats">';
  var kd = p.kd || p.avg_kd || 0, kad = p.kad || p.avg_kad || 0, kp = p.kp || p.avg_kp || 0;
  [["Kills", p.kills, 1], ["Assists", p.assists, 1], ["Damage", p.dmg, 1], ["K/D", kd, 1], ["KA/D", kad, 1], ["KP%", kp + "%", 0], ["Games", p.games, 0]].forEach(function(s) {
    h += '<div class="modal-stat"><div class="label">' + s[0] + '</div><div class="value' + (s[2] ? ' hl' : '') + '">' + s[1] + '</div></div>';
  });
  h += '</div>';
  document.getElementById("modal-content").innerHTML = h;
  document.getElementById("modal").classList.add("active");
}
function hideModal() { document.getElementById("modal").classList.remove("active"); }
document.addEventListener("keydown", function(e) { if (e.key === "Escape") hideModal(); });
</script>
</body>
</html>
'''
html = html.replace("__JSON_PLACEHOLDER__", json_str)

output_path = os.path.join(PUBLIC_DIR, "index.html")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)
html_kb = os.path.getsize(output_path) / 1024
print(f"\nHTML: {html_kb:.0f} KB")
print(f"Thumbs: {len(os.listdir(THUMBS_DIR))} files")
print(f"Photos: {len(os.listdir(PHOTOS_DIR))} files")
print(f"Output: {output_path}")
