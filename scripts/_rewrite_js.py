#!/usr/bin/env python3
"""Rewrite build_app.py JS section for dropdown group stage"""
import os

path = r"D:\algs player data\build_app.py"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()

# Find old JS
old_start = "<script>\nvar DATA = "
old_end = "</script>\n</body>\n</html>"
s = c.find(old_start)
e = c.find(old_end)

new_js = '''<script>
var DATA = ''' + '''json_str''' + '''r''';
var playerMode = "list";
var currentGroup = "overall";
var GROUPS = ["ab","ac","ad","bc","bd","cd"];
var GROUP_LABELS = {"ab":"Day1 A vs B","ac":"Day2 A vs C","ad":"Day3 A vs D","bc":"Day3 B vs C","bd":"Day2 B vs D","cd":"Day1 C vs D"};

(function init(){
  var tabs=document.getElementById("tabs");
  addTab("overall","Overall Standings");
  addTab("all","All Players");
  var dd=document.createElement("div");dd.className="tab-dd";dd.id="group-dd";
  var btn=document.createElement("button");btn.className="tab-btn";btn.textContent="Group Stage";btn.id="dd-btn";
  btn.onclick=function(e){e.stopPropagation();dd.classList.toggle("open");};
  tabs.appendChild(btn);
  GROUPS.forEach(function(g){
    var b=document.createElement("button");b.className="tab-btn dd-item";b.textContent=GROUP_LABELS[g];
    b.onclick=function(e){e.stopPropagation();dd.classList.remove("open");switchGroup(g);};
    dd.appendChild(b);
  });
  tabs.appendChild(dd);
  document.addEventListener("click",function(){dd.classList.remove("open");});
  ["overall","all"].concat(GROUPS).forEach(function(g){
    var p=document.createElement("div");p.className="tab-panel";p.id="panel-"+g;document.getElementById("content").appendChild(p);
  });
  switchGroup("overall");
})();

function addTab(g,label){
  var btn=document.createElement("button");btn.className="tab-btn";btn.textContent=label;
  btn.onclick=function(){switchGroup(g);};
  document.getElementById("tabs").appendChild(btn);
}

function switchGroup(g){
  currentGroup=g;
  var dd=document.getElementById("group-dd");
  if(dd)dd.classList.remove("open");
  document.querySelectorAll(".tab-btn:not(.dd-item)").forEach(function(b){b.classList.toggle("active",b.textContent===DATA[g].label)});
  document.querySelectorAll(".tab-panel").forEach(function(p){p.classList.toggle("active",p.id==="panel-"+g)});
  renderPanel(g);
}

function renderPanel(g){
  var d=DATA[g], panel=document.getElementById("panel-"+g), h="";
  if(g==="overall"){
    h+='<div class="stats-bar"><div class="stat-box"><div class="num">40</div><div class="lbl">Teams</div></div>';
    h+='<div class="stat-box"><div class="num" style="color:#00ff88">14</div><div class="lbl">Finals</div></div>';
    h+='<div class="stat-box"><div class="num" style="color:#ffd700">20</div><div class="lbl">Survivor</div></div>';
    h+='<div class="stat-box"><div class="num" style="color:#ff4444">6</div><div class="lbl">Eliminated</div></div></div>';
    h+='<div class="table-wrap"><table><thead><tr><th>#</th><th>Team</th><th>G</th><th>Score</th><th>Status</th></tr></thead><tbody>';
    d.standings.forEach(function(s){
      var c=s.status==="Finals"?"#00ff88":s.status==="Survivor"?"#ffd700":"#ff4444";
      h+='<tr><td>'+s.rank+'</td><td><strong>'+s.team+'</strong></td><td>G'+s.group+'</td><td><strong>'+s.score+'</strong></td><td style="color:'+c+'">'+s.status+'</td></tr>';
    });
    h+='</tbody></table></div>';panel.innerHTML=h;return;
  }

  h+='<div class="stats-bar">';
  h+='<div class="stat-box"><div class="num">'+d.player_count+'</div><div class="lbl">Players</div></div>';
  h+='<div class="stat-box"><div class="num">'+d.team_count+'</div><div class="lbl">Teams</div></div>';
  h+='<div class="stat-box"><div class="num">'+(d.groups?d.groups.join(" vs "):"All")+'</div><div class="lbl">Groups</div></div></div>';

  if(g==="all"){
    h+='<div class="table-wrap" style="max-height:250px;margin-bottom:12px"><table><thead><tr><th>#</th><th>Team</th><th>Kills</th><th>Damage</th></tr></thead><tbody>';
    var mk=d.teams[0]?d.teams[0].kills:1;
    d.teams.forEach(function(t,i){h+='<tr><td>'+(i+1)+'</td><td><strong>'+t.name+'</strong></td><td>'+t.kills+'</td><td>'+t.dmg.toLocaleString()+'</td></tr>';});
    h+='</tbody></table></div>';
  }

  h+='<div class="sub-bar">';
  h+='<button class="view-btn'+(playerMode==="list"?" active":"")+'" onclick="playerMode=\\'list\\';renderPanel(\\''+g+'\\')">List</button>';
  if(g!=="all")h+='<button class="view-btn'+(playerMode==="radar"?" active":"")+'" onclick="playerMode=\\'radar\\';renderPanel(\\''+g+'\\')">Radar Charts</button>';
  h+='</div>';

  h+='<div class="view-panel'+(playerMode==="list"?" active":"")+'">';
  var ph=g==="all"?["#","Player","Team","G","M","K","A","Dmg","KD","KAD","KP%"]:["#","Player","Team","K","A","Dmg","K/D","KA/D","KP%"];
  h+='<div class="table-wrap"><table><thead><tr>';ph.forEach(function(x){h+='<th>'+x+'</th>'});h+='</tr></thead><tbody>';
  d.players.forEach(function(p,i){
    h+='<tr class="player-row" onclick="showDetail(\\''+g+'\\','+i+')"><td>'+(i+1)+'</td><td><strong>'+p.name+'</strong></td><td>'+p.team+'</td>';
    if(g==="all"){h+='<td>'+p.games+'</td><td>'+p.matches+'</td>';}
    h+='<td>'+p.kills+'</td><td>'+p.assists+'</td><td>'+p.dmg+'</td><td>'+(g==="all"?p.avg_kd:p.kd)+'</td><td>'+(g==="all"?p.avg_kad:p.kad)+'</td><td>'+(g==="all"?p.avg_kp:p.kp)+'%</td></tr>';
  });
  h+='</tbody></table></div></div>';

  if(g!=="all"){
    h+='<div class="view-panel'+(playerMode==="radar"?" active":"")+'"><div class="radar-grid">';
    d.players.forEach(function(p,i){if(p.thumb)h+='<div class="radar-card" onclick="showDetail(\\''+g+'\\','+i+')"><img src="'+p.thumb+'" alt="'+p.name+'" loading="lazy"><div class="rname">'+p.name+'</div><div class="rteam">'+p.team+'</div></div>';});
    h+='</div></div>';
  }
  panel.innerHTML=h;
}

function showDetail(g,idx){
  var p=DATA[g].players[idx], h='<div class="modal-header">';
  if(p.thumb)h+='<img class="modal-radar" src="'+p.thumb+'">';
  if(p.photo)h+='<img class="modal-photo" src="'+p.photo+'">';
  h+='<div class="modal-title"><h2>'+p.name+'</h2><div class="team">'+p.team+'</div></div></div>';
  h+='<div class="modal-stats">';
  [["Kills",p.kills,1],["Assists",p.assists,1],["Damage",p.dmg,1],["K/D",p.kd||p.avg_kd,1],["KA/D",p.kad||p.avg_kad,1],["KP%",(p.kp||p.avg_kp)+"%",0],["Games",p.games,0]].forEach(function(s){h+='<div class="modal-stat"><div class="label">'+s[0]+'</div><div class="value'+(s[2]?' hl':'')+'">'+s[1]+'</div></div>';});
  h+='</div>';
  document.getElementById("modal-content").innerHTML=h;
  document.getElementById("modal").classList.add("active");
}
function hideModal(){document.getElementById("modal").classList.remove("active");}
document.addEventListener("keydown",function(e){if(e.key==="Escape")hideModal();});
</script>
</body>
</html>'''

# Fix: proper Python code generation
# The issue is json_str needs to be spliced into the JS code
# Current build_app.py generates: var DATA = ''' + json_str + r''';
# Let me fix this part
old_dataline = "var DATA = ''' + json_str + r'''"
new_dataline = new_js.split('\n')[0]  # var DATA = ... from new_js

# Actually, simpler approach: just replace the HTML body section
body_start = c.find('<script>\nvar DATA = ')
body_end = c.find('</script>\n</body>\n</html>')

if body_start < 0:
    print("ERROR: Could not find script section")
    exit(1)

# Build the correct JS section with json_str interpolation
correct_js = new_js.replace("''' + '''json_str''' + '''r'''", "''' + json_str + r'''")

# Verify
if "json_str" not in correct_js or "var DATA = " not in correct_js:
    print("ERROR: json_str not in template")
    exit(1)

c = c[:body_start] + correct_js

# Add dropdown CSS
drop_css = '''
/* Dropdown */
.tab-dd{display:none;position:absolute;top:100%;left:0;background:#14142e;border:1px solid #2a2a4e;border-radius:10px;padding:4px;z-index:100;min-width:170px;margin-top:4px}
.tab-dd.open{display:block}
.tab-dd .tab-btn{display:block;width:100%;margin:2px 0;text-align:left}
.tabs{position:relative}'''

c = c.replace('@media(max-width:600px)', drop_css + '\n@media(max-width:600px)')

with open(path, "w", encoding="utf-8") as f:
    f.write(c)

print("JS section replaced. Verifying...")
# Quick check
if 'function renderPanel(g)' in c and 'switchGroup' in c and 'tab-dd' in c:
    print("OK - all key components present")
else:
    print("WARN - something missing")
