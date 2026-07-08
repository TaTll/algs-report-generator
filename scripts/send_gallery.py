#!/usr/bin/env python3
"""
将雷达图拼成大图 + 生成交互式画廊HTML + 发送到飞书
用法: python send_gallery.py [--skip-feishu]
"""
import requests
import sys
import json
import os
import sys
import base64
from math import ceil

# 强制 UTF-8
sys.stdout.reconfigure(encoding='utf-8')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image

# 导入战队映射和选手照片查找工具
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from team_utils import find_player_photo, get_player_photo_base64, get_team_abbr, find_team_logo, get_match_title

WEBHOOK_URL = os.environ.get('FEISHU_WEBHOOK_URL', '')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Auto-load from config file if env not set
if not WEBHOOK_URL:
    config_file = os.path.join(BASE_DIR, '.feishu_config')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            WEBHOOK_URL = f.read().strip()
        os.environ['FEISHU_WEBHOOK_URL'] = WEBHOOK_URL
ROOT_DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
DATA_DIR = os.environ.get('BH_DATA_DIR', ROOT_DATA_DIR)
CHART_DIR = os.path.join(DATA_DIR, 'radar_charts')
PICTURE_DIR = os.path.join(ROOT_DATA_DIR, 'picture-ab')
CSV_PATH = os.path.join(DATA_DIR, 'algs_players_data.csv')

# 自动推断比赛标题
MATCH_TITLE, MATCH_SUBTITLE = get_match_title(CSV_PATH)
print(f"比赛: {MATCH_TITLE}")

# ====== 1. 生成拼图 ======
print("正在合成雷达图拼图...")

# 收集所有雷达图路径
chart_files = sorted([f for f in os.listdir(CHART_DIR) if f.endswith('.png')])
print(f"找到 {len(chart_files)} 张雷达图")

# 设置网格参数
COLS = 8
ROWS = ceil(len(chart_files) / COLS)
THUMB_W, THUMB_H = 300, 300
GRID_GAP = 5

canvas_w = COLS * THUMB_W + (COLS - 1) * GRID_GAP + 40
canvas_h = ROWS * THUMB_H + (ROWS - 1) * GRID_GAP + 80 + 60

canvas = Image.new('RGB', (canvas_w, canvas_h), (15, 15, 35))
from PIL import ImageDraw, ImageFont

draw = ImageDraw.Draw(canvas)
try:
    font = ImageFont.truetype("arial.ttf", 18)
except:
    font = ImageFont.load_default()

draw.text((canvas_w//2 - 150, 15), f"{MATCH_TITLE} 选手雷达图", fill=(0, 210, 255), font=font)
draw.text((canvas_w//2 - 100, canvas_h - 25), f"共 {len(chart_files)} 名选手", fill=(100, 100, 120), font=font)

for idx, fname in enumerate(chart_files):
    row = idx // COLS
    col = idx % COLS
    x = 20 + col * (THUMB_W + GRID_GAP)
    y = 50 + row * (THUMB_H + GRID_GAP)

    img = Image.open(os.path.join(CHART_DIR, fname))
    img = img.resize((THUMB_W, THUMB_H), Image.LANCZOS)
    canvas.paste(img, (x, y))

    # 选手名
    name = fname.replace('.png', '').replace('_', ' ')
    if len(name) > 18:
        name = name[:16] + '..'
    # Draw name below thumbnail
    draw.text((x, y + THUMB_H + 2), name, fill=(200, 200, 200), font=font)

collage_path = os.path.join(DATA_DIR, 'radar_collage.jpg')
canvas.save(collage_path, 'JPEG', quality=75)
print(f"拼图已保存: {collage_path} ({canvas.size})")

print("创建嵌入式网页...")

# 将所有雷达图转为base64嵌入到HTML中
# 为了减小大小，只嵌入缩略图版本
html_path = os.path.join(DATA_DIR, 'radar_gallery.html')

# 生成每个选手的数据行
csv_path = os.path.join(DATA_DIR, 'algs_players_data.csv')
player_rows = []
with open(csv_path, 'r', encoding='utf-8-sig') as f:
    import csv
    reader = csv.DictReader(f)
    for row in reader:
        player_rows.append(row)

# Generate embedded JSON for PLAYER_DATA (avoids fetch CORS issue when opened locally)
import json as _json
_player_data_js = 'var PLAYER_DATA = ' + _json.dumps(player_rows, ensure_ascii=False) + ';\n'

# 生成带base64图片的HTML（用缩略图控制大小）
img_data_map = {}
for fname in chart_files:
    name_key = fname.replace('.png', '')
    img = Image.open(os.path.join(CHART_DIR, fname))
    img.thumbnail((600, 600), Image.LANCZOS)
    import io
    buf = io.BytesIO()
    img.save(buf, 'PNG')
    b64 = base64.b64encode(buf.getvalue()).decode()
    img_data_map[name_key] = b64

print(f"已嵌入 {len(img_data_map)} 张图片到HTML")

# ---- 预加载选手照片 base64 ----
photo_data_map = {}
photo_count_embedded = 0
for p in player_rows:
    name = p.get('Player', '')
    team = p.get('Team', '')
    b64 = get_player_photo_base64(name, team_name=team, max_size=(240, 240))
    if b64:
        name_key = name.lower().strip()
        photo_data_map[name_key] = b64
        photo_count_embedded += 1

_photo_js_parts = []
for name_key, b64 in photo_data_map.items():
    _photo_js_parts.append(f'"{name_key}": "{b64}"')
player_photo_js = 'var PLAYER_PHOTOS = {' + ','.join(_photo_js_parts) + '};\n'
print(f"已嵌入 {photo_count_embedded} 张选手照片到HTML")

# ---- 预加载战队Logo base64 ----
logo_data_map = {}
logo_count_embedded = 0
# Collect unique team abbreviations from player data
team_abbrs_seen = set()
for p in player_rows:
    team = p.get('Team', '')
    abbr = get_team_abbr(team)
    if abbr and abbr not in team_abbrs_seen:
        team_abbrs_seen.add(abbr)
        logo_path = find_team_logo(team_abbr=abbr)
        if logo_path:
            try:
                logo_img = Image.open(logo_path)
                logo_img.thumbnail((80, 80), Image.LANCZOS)
                buf = io.BytesIO()
                logo_img.save(buf, 'PNG')
                logo_data_map[abbr] = base64.b64encode(buf.getvalue()).decode()
                logo_count_embedded += 1
            except Exception:
                pass

_logo_js_parts = []
for abbr, b64 in logo_data_map.items():
    _logo_js_parts.append(f'"{abbr}": "{b64}"')
team_logo_js = 'var TEAM_LOGOS = {' + ','.join(_logo_js_parts) + '};\n'
print(f"已嵌入 {logo_count_embedded} 个战队Logo到HTML")

# 构建可搜索的HTML画廊
gallery_html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>''' + MATCH_TITLE + ''' 选手数据画廊</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, 'Segoe UI', Arial, sans-serif; background: #0f0f23; color: #eee; padding: 20px; }
h1 { color: #00d2ff; text-align: center; margin-bottom: 5px; font-size: 24px; }
.subtitle { text-align: center; color: #888; margin-bottom: 20px; font-size: 14px; }
.search-box { text-align: center; margin-bottom: 20px; }
.search-box input { width: 80%; max-width: 400px; padding: 10px 16px; border-radius: 20px; border: 1px solid #333;
  background: #1a1a2e; color: #eee; font-size: 14px; outline: none; }
.search-box input:focus { border-color: #00d2ff; }
.gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 20px; }
.card { background: #1a1a2e; border-radius: 12px; overflow: hidden; border: 1px solid #2a2a4e; transition: transform .2s; }
.card:hover { transform: scale(1.03); border-color: #00d2ff; cursor: pointer; }
.card img { width: 100%; display: block; }
.card-body { padding: 10px 14px 14px; }
.card-name { color: #00d2ff; font-weight: bold; font-size: 15px; }
.card-team { color: #aaa; font-size: 12px; display: flex; align-items: center; gap: 6px; }
.card-logo { width: 22px; height: 22px; object-fit: contain; border-radius: 4px; flex-shrink: 0; }
.card-stats { display: flex; flex-wrap: wrap; gap: 4px 12px; margin-top: 6px; font-size: 12px; }
.stat { background: #16213e; padding: 2px 8px; border-radius: 8px; color: #ccc; }
.stat strong { color: #fff; }
.footer { text-align: center; color: #555; margin-top: 30px; font-size: 12px; }
.hidden { display: none; }

/* Player photo in modal */
.modal-photo { width: 140px; height: 140px; border-radius: 50%; object-fit: cover; border: 3px solid #00d2ff; flex-shrink: 0; background: #16213e; }
.modal-photo-placeholder { width: 140px; height: 140px; border-radius: 50%; border: 3px dashed #333; flex-shrink: 0; display: flex; align-items: center; justify-content: center; color: #555; font-size: 12px; }
.modal-logo { width: 48px; height: 48px; object-fit: contain; border-radius: 6px; flex-shrink: 0; }

/* Modal */
.modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; justify-content: center; align-items: center; }
.modal-overlay.active { display: flex; }
.modal-box { background: #1a1a2e; border: 2px solid #00d2ff; border-radius: 16px; padding: 30px; max-width: 750px; width: 95%; max-height: 90vh; overflow-y: auto; position: relative; animation: modalIn .25s ease; }
@keyframes modalIn { from { opacity: 0; transform: scale(.9); } to { opacity: 1; transform: scale(1); } }
.modal-close { position: absolute; top: 12px; right: 18px; background: none; border: none; color: #888; font-size: 28px; cursor: pointer; line-height: 1; }
.modal-close:hover { color: #fff; }
.modal-header { display: flex; align-items: flex-start; gap: 20px; margin-bottom: 24px; flex-wrap: wrap; }
.modal-header .radar-wrapper { position: relative; display: inline-block; flex-shrink: 0; margin: 22px 22px 22px 0; }
.modal-header .radar-wrapper img { width: 280px; display: block; border-radius: 10px; }
/* Radar axis labels around the image (hexagon positions) */
.radax { position: absolute; font-size: 11px; font-weight: bold; color: #fff;
  background: rgba(0,0,0,0.75); padding: 3px 8px; border-radius: 8px;
  white-space: nowrap; pointer-events: none; border: 1px solid #00d2ff;
  line-height: 1.3; text-align: center; z-index: 5; }
.radax .val { color: #00d2ff; }
.radax-0 { right: -10px; top: 50%; transform: translateY(-50%); }   /* right → KP% */
.radax-1 { top: -18px; right: 15%; }                                  /* top-right → Dmg */
.radax-2 { top: -18px; left: 15%; }                                   /* top-left → KA/D */
.radax-3 { left: -10px; top: 50%; transform: translateY(-50%); }      /* left → Kills */
.radax-4 { bottom: -18px; left: 15%; }                                /* bottom-left → Assists */
.radax-5 { bottom: -18px; right: 15%; }                               /* bottom-right → K/D */
.modal-title h2 { color: #00d2ff; margin: 0 0 4px; font-size: 22px; }
.modal-title .team { color: #aaa; font-size: 14px; margin: 0 0 6px; }
.modal-title .badge { display: inline-block; background: #0f3460; color: #00d2ff; padding: 3px 12px; border-radius: 12px; font-size: 13px; margin-right: 8px; }
.modal-stats { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 10px; }
.modal-stat { background: #16213e; border-radius: 10px; padding: 12px 14px; }
.modal-stat .label { color: #888; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }
.modal-stat .value { color: #fff; font-size: 20px; font-weight: bold; margin-top: 2px; }
.modal-stat .value.highlight { color: #00d2ff; }
</style>
</head>
<body>
<h1>🏆 ''' + MATCH_TITLE + '''</h1>
<p class="subtitle">''' + MATCH_SUBTITLE + ''' · 点击图片可放大 · 搜索框可筛选</p>
<div class="search-box"><input type="text" id="search" placeholder="搜索选手姓名或队伍..." oninput="filterCards()"></div>
<div class="gallery" id="gallery">
'''

for p in player_rows:
    name = p.get('Player', '')
    team = p.get('Team', '')
    group = p.get('Group', '')
    kills = p.get('Kills', '0')
    dmg = p.get('DmgDealt', '0')
    kad = p.get('KAD', '0')
    kp = p.get('KillParticipationPct', '0')
    kd = p.get('KD', '0')
    bestp = p.get('BestP', '')
    assists = p.get('Assists', '0')
    knocks = p.get('Knocks', '0')

    name_slug = name.replace(' ', '_').replace('/', '_')
    # Remove chars not valid in filenames
    import re as _re
    name_slug = _re.sub(r'[^a-zA-Z0-9_-]', '_', name_slug)
    b64_img = img_data_map.get(name_slug, '')

    # Team logo
    team_abbr = get_team_abbr(team)
    logo_html = ''
    if team_abbr and team_abbr in logo_data_map:
        logo_html = f'<img class="card-logo" src="data:image/png;base64,{logo_data_map[team_abbr]}" alt="{team_abbr}">'

    gallery_html += f'''<div class="card" data-name="{name.lower()}" data-team="{team.lower()}" data-abbr="{team_abbr or ''}">
  <img src="data:image/png;base64,{b64_img}" alt="{name}" onclick="showDetail(this)">
  <div class="card-body">
    <div class="card-name">{name}</div>
    <div class="card-team">{logo_html}{team} | Group {group} | Best: {bestp}</div>
    <div class="card-stats">
      <span class="stat">击杀 <strong>{kills}</strong></span>
      <span class="stat">助攻 <strong>{assists}</strong></span>
      <span class="stat">伤害 <strong>{dmg}</strong></span>
      <span class="stat">KA/D <strong>{kad}</strong></span>
      <span class="stat">K/D <strong>{kd}</strong></span>
      <span class="stat">参与率 <strong>{kp}%</strong></span>
      <span class="stat">击倒 <strong>{knocks}</strong></span>
    </div>
  </div>
</div>
'''

gallery_html += '''</div>
<!-- 详情弹窗 -->
<div class="modal-overlay" id="modal" onclick="hideDetail(event)">
  <div class="modal-box" onclick="event.stopPropagation()">
    <button class="modal-close" onclick="hideDetail()">&times;</button>
    <div id="modal-content"></div>
  </div>
</div>
<div class="footer">数据来源: apexlegendsstatus.com · 由 ALGS Data Tool 生成</div>
<script>
var PLAYER_DATA = null;
''' + _player_data_js + '''
''' + player_photo_js + '''
''' + team_logo_js + '''


function findPlayer(name) {
  if (!PLAYER_DATA) return null;
  name = name.toLowerCase().replace(/\\s+/g, ' ').trim();
  for (var i = 0; i < PLAYER_DATA.length; i++) {
    var p = PLAYER_DATA[i];
    var pname = (p.Player || '').toLowerCase().replace(/\\s+/g, ' ').trim();
    if (pname === name) return p;
  }
  return null;
}

function showDetail(img) {
  var card = img.closest('.card');
  var nameEl = card.querySelector('.card-name');
  if (!nameEl) return;
  var playerName = nameEl.textContent.trim();

  var data = findPlayer(playerName);
  var imgSrc = img.getAttribute('src');

  var html = '<div class="modal-header">';

  // ---- Player photo (if available) ----
  var photoKey = playerName.toLowerCase().trim();
  var photoB64 = (typeof PLAYER_PHOTOS !== 'undefined' && PLAYER_PHOTOS) ? PLAYER_PHOTOS[photoKey] : null;
  if (photoB64) {
    html += '<img class="modal-photo" src="data:image/png;base64,' + photoB64 + '" alt="' + playerName + '">';
  } else {
    html += '<div class="modal-photo-placeholder">No Photo</div>';
  }
  // ---- Team logo in modal ----
  var teamAbbr = '';
  if (data && data.Team) {
    // Find abbr from card dataset
    var abbrFromCard = card.dataset.abbr;
    if (abbrFromCard && (typeof TEAM_LOGOS !== 'undefined' && TEAM_LOGOS) && TEAM_LOGOS[abbrFromCard]) {
      teamAbbr = abbrFromCard;
      html += '<img class="modal-logo" src="data:image/png;base64,' + TEAM_LOGOS[abbrFromCard] + '" alt="' + teamAbbr + '">';
    }
  }
  // Radar image with 6 axis labels overlaid around it
  html += '<div class="radar-wrapper">';
  html += '<img src="' + imgSrc + '" alt="' + playerName + '">';
  if (data) {
    html += '<div class="radax radax-0">KP%<br><span class="val">' + (data.KillParticipationPct || '0') + '%</span></div>';
    html += '<div class="radax radax-1">Dmg<br><span class="val">' + (data.DmgDealt || '0') + '</span></div>';
    html += '<div class="radax radax-2">KA/D<br><span class="val">' + (data.KAD || '0') + '</span></div>';
    html += '<div class="radax radax-3">Kills<br><span class="val">' + (data.Kills || '0') + '</span></div>';
    html += '<div class="radax radax-4">Assists<br><span class="val">' + (data.Assists || '0') + '</span></div>';
    html += '<div class="radax radax-5">K/D<br><span class="val">' + (data.KD || '0') + '</span></div>';
  }
  html += '</div>';
  html += '<div class="modal-title">';
  html += '<h2>' + playerName + '</h2>';
  if (data) {
    html += '<p class="team">' + (data.Team || '') + ' | Group ' + (data.Group || '') + ' | Best: ' + (data.BestP || '') + '</p>';
    html += '<span class="badge">' + (data.Games || '0') + ' 场</span>';
    html += '<span class="badge">存活 ' + (data.SurvTime || '0') + '</span>';
    html += '</div></div>';
    html += '<div class="modal-stats">';
    html += statBox('击杀 Kills', data.Kills, true);
    html += statBox('助攻 Assists', data.Assists, true);
    html += statBox('伤害 Dmg', data.DmgDealt, true);
    html += statBox('K/D', data.KD, true);
    html += statBox('KA/D', data.KAD, true);
    html += statBox('击杀参与率', data.KillParticipationPct + '%', false);
    html += statBox('击倒 Knocks', data.Knocks, false);
    html += statBox('被击倒', data.TimesKnocked, false);
    html += statBox('承受伤害', data.DmgTaken, false);
    html += statBox('伤害差值', data.DmgDiff, false);
    html += statBox('每杀伤害', data.DmgPerKill, false);
    html += statBox('毒圈伤害', data.RingDmg, false);
    html += statBox('复活次数', data.Rez, false);
    html += statBox('重生次数', data.Rspn, false);
    html += statBox('死亡次数', data.Deaths, false);
    html += '</div>';
  } else {
    html += '<p class="team">数据加载中或未找到...</p>';
    html += '</div></div>';
  }
  document.getElementById('modal-content').innerHTML = html;
  document.getElementById('modal').classList.add('active');
}

function statBox(label, value, highlight) {
  var vcls = highlight ? 'value highlight' : 'value';
  return '<div class="modal-stat"><div class="label">' + label + '</div><div class="' + vcls + '">' + (value || '0') + '</div></div>';
}

function hideDetail(e) {
  if (e && e.target !== document.getElementById('modal')) return;
  document.getElementById('modal').classList.remove('active');
}

document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') document.getElementById('modal').classList.remove('active');
});

function filterCards() {
  var q = document.getElementById('search').value.toLowerCase();
  document.querySelectorAll('.card').forEach(function(c) {
    c.classList.toggle('hidden', q && !c.dataset.name.includes(q) && !c.dataset.team.includes(q));
  });
}
</script>
</body>
</html>'''

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(gallery_html)

html_size_mb = os.path.getsize(html_path) / (1024*1024)
print(f"画廊网页已生成: {html_path} ({html_size_mb:.1f} MB)")

# ====== 4. 发送通知到飞书 ======
if '--skip-feishu' not in sys.argv and WEBHOOK_URL:
    print("发送飞书通知...")

    def send_feishu(file_path, file_type="file"):
        """上传文件到飞书群"""
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)

        try:
            with open(file_path, 'rb') as f:
                r = requests.post(
                    WEBHOOK_URL,
                    files={'file': (file_name, f)},
                    data={'msg_type': 'file'},
                    timeout=60
                )
            print(f"飞书文件上传响应: {r.json()}")
        except Exception as e:
            print(f"文件上传失败: {e}")

        msg = {
            "msg_type": "text",
            "text": {
                "content": f"✅ ALGS 选手数据已生成完毕\n\n雷达图: {len(chart_files)} 张\nHTML画廊: {file_name}\n目录: {DATA_DIR}"
            }
        }
        r = requests.post(WEBHOOK_URL, json=msg, timeout=15)
        print(f"飞书通知响应: {r.json()}")

    send_feishu(html_path)
else:
    print("(跳过飞书发送)" if WEBHOOK_URL else "(未配置 FEISHU_WEBHOOK_URL，跳过飞书发送)")

print(f"\n✅ 全部完成！HTML画廊: {html_path}")
