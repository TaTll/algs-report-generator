#!/usr/bin/env python3
"""
战队名称 → 缩写映射 & 选手照片查找工具
用于在报告生成中嵌入选手照片和战队Logo
"""
import os
import re
import csv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
PICTURE_DIR = os.path.join(ROOT_DATA_DIR, 'picture-ab')
DATA_DIR = os.environ.get('BH_DATA_DIR', ROOT_DATA_DIR)

# Day detection: which group pairs map to which day
# Based on Group Stage schedule:
# Day1: AvB, CvD | Day2: BvD, AvC | Day3: BvC, AvD
GROUP_DAY_MAP = {
    ('A', 'B'): 1, ('B', 'A'): 1,
    ('C', 'D'): 1, ('D', 'C'): 1,
    ('B', 'D'): 2, ('D', 'B'): 2,
    ('A', 'C'): 2, ('C', 'A'): 2,
    ('B', 'C'): 3, ('C', 'B'): 3,
    ('A', 'D'): 3, ('D', 'A'): 3,
}


def get_match_title(csv_path=None, event_name="ALGS Y6 Split1 Playoffs"):
    """
    从 CSV 文件的 Group 列推断比赛标题。
    返回: (title, subtitle) 例如 ("ALGS Y6 Split1 Playoffs - Day2 B vs D", "B vs D · 60 players")
    """
    if csv_path is None:
        csv_path = os.path.join(DATA_DIR, 'algs_players_data.csv')

    dataset_name = os.path.basename(os.path.dirname(os.path.abspath(csv_path))).lower()
    
    groups = set()
    player_count = 0
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                g = row.get('Group', '').strip()
                if g:
                    groups.add(g)
                player_count += 1
    except Exception:
        return (f"{event_name}", f"{player_count} players")

    if dataset_name == 'fn':
        return f"{event_name} - Finals", f"Finals · {player_count} players"
    if dataset_name == 'sf':
        return f"{event_name} - Survivor Stage", f"Survivor Stage · {player_count} players"
    
    groups_sorted = sorted(groups)
    groups_str = ' vs '.join(groups_sorted)
    
    # Detect day
    day = None
    if len(groups_sorted) == 2:
        key = (groups_sorted[0], groups_sorted[1])
        day = GROUP_DAY_MAP.get(key)
    
    if day:
        title = f"{event_name} - Day{day} {groups_str}"
    else:
        title = f"{event_name} - {groups_str}"
    
    subtitle = f"{groups_str} · {player_count} players"
    return title, subtitle


# ====== 精确映射: 战队全名 → 缩写（来自 Liquipedia Group Stage） ======
EXACT_TEAM_MAP = {
    "All Gamers Global": "AGG",
    "Alliance": "ALL",
    "Aurora Gaming": "AUR",
    "DINOS": "DINOS",
    "Deep Cross Gaming": "DCG",
    "Dogred": "DOG",
    "Dory": "DORY",
    "ENTER FORCE.36": "E36",
    "Elite Esports Europe": "EE.EU",
    "Flat": "FLAT",
    "For Fun Esports": "FF",
    "Gaimin Gladiators": "GG",
    "Geekay Esports": "GK",
    "Gen.G Esports": "GEN",
    "JD Gaming": "JDG",
    "KINOTROPE Club": "KNC",
    "Kirisame Havoc": "KSH",
    "Ninjas in Pyjamas": "NIP",
    "Pork Xiaolongbao Xpert": "PXX",
    "REJECT": "RC",
    "Rex Regum Qeon": "RRQ",
    "S8UL Esports": "S8UL",
    "Sentinels": "SEN",
    "Shopify Rebellion": "SR",
    "TIE": "TIE",
    "TLN Pirates": "TLN",
    "Team Falcons": "FLCN",
    "Team Heretics": "TH",
    "Team Liquid": "TL",
    "Team Nemesis": "NEM",
    "Team Vision": "VSN",
    "TriniTY": "TTY",
    "UNLIMIT": "UNL",
    "VK Gaming": "VKG",
    "Virtus.pro": "VP",
    "White Grim Reaper NEO": "WGR.N",
    "Wolves Esports": "WOL",
    "ZEDI ESPORTS": "ZEDI",
    "ZETA DIVISION": "ZETA",
    "ZiPLine Mafia": "ZIP",
}

# ====== 模糊匹配表: CSV中可能出现的变体 → 缩写 ======
# 用于 apexlegendsstatus.com 的CSV导出数据（队名可能简化/大小写不同）
FUZZY_TEAM_MAP = {
    # 大小写变体
    "aurora": "AUR", "aurora gaming": "AUR",
    "alliance": "ALL",
    "dinos": "DINOS",
    "dogred": "DOG",
    "dory": "DORY",
    "enter force.36": "E36", "enter force 36": "E36",
    "elite esports": "EE.EU", "elite esports europe": "EE.EU",
    "flat": "FLAT",
    "for fun esports": "FF",
    "gaimin gladiators": "GG",
    "geekay esports": "GK",
    "gen.g esports": "GEN", "gen.g": "GEN", "geng": "GEN",
    "jd gaming": "JDG",
    "kinotrope club": "KNC",
    "kirisame havoc": "KSH",
    "ninjas in pyjamas": "NIP", "ninjasinpyjamas": "NIP",
    "pork xiaolongbao xpert": "PXX",
    "reject": "RC",
    "rex regum qeon": "RRQ", "team rrq": "RRQ",
    "s8ul esports": "S8UL", "s8ul": "S8UL",
    "sentinels": "SEN",
    "shopify rebellion": "SR",
    "tie": "TIE",
    "tln pirates": "TLN",
    "team falcons": "FLCN", "falcons": "FLCN",
    "team heretics": "TH", "heretics": "TH",
    "team liquid": "TL", "liquid": "TL",
    "team nemesis": "NEM", "nemesis": "NEM",
    "team vision": "VSN",
    "trinity": "TTY",
    "unlimit": "UNL",
    "vk gaming": "VKG", "vk": "VKG",
    "virtus.pro": "VP", "virtus pro": "VP", "vp": "VP",
    "white grim reaper neo": "WGR.N", "wgr neo": "WGR.N",
    "wolves esports": "WOL", "wolves": "WOL",
    "zedi esports": "ZEDI", "zedi": "ZEDI",
    "zeta division": "ZETA", "zeta": "ZETA",
    "zipline mafia": "ZIP", "zip": "ZIP",
    # apexlegendsstatus.com specific variants
    "all gamers global": "AGG",
    "deep cross gaming": "DCG",
    "s8ul esports": "S8UL",
    "s8ul": "S8UL",
    "elite esports": "EE.EU",
    "team rrq": "RRQ",
    "vk gaming": "VKG",
    "wgr neo": "WGR.N",
    "zipline mafia": "ZIP",
    "kinotrope club": "KNC",
    "ninjasinpyjamas": "NIP",
}

# ====== 缓存：扫描 picture-ab 目录建立 player→abbr 反向索引 ======
_player_abbr_cache = None
_picture_files_cache = None


def _list_picture_files():
    """Return cached filenames from picture-ab to avoid repeated directory scans."""
    global _picture_files_cache
    if _picture_files_cache is not None:
        return _picture_files_cache

    if not os.path.isdir(PICTURE_DIR):
        _picture_files_cache = []
    else:
        _picture_files_cache = os.listdir(PICTURE_DIR)
    return _picture_files_cache


def _is_usable_asset(path, min_size=5000):
    """Small guard against placeholder/broken image assets."""
    return os.path.exists(path) and os.path.getsize(path) > min_size


def _find_asset_by_filename(filename):
    """Case-insensitive lookup in picture-ab, returning an absolute path."""
    filename_lower = filename.lower()
    for existing in _list_picture_files():
        if existing.lower() == filename_lower:
            path = os.path.join(PICTURE_DIR, existing)
            if _is_usable_asset(path):
                return path
    return None


def _find_photo_by_abbr_and_player(team_abbr, player_name):
    """Try direct player-photo filename patterns for one team abbreviation."""
    if not team_abbr or not player_name:
        return None

    player_variants = {
        player_name,
        player_name.replace(' ', '_'),
        re.sub(r'\s+', '_', player_name.strip()),
    }
    for player_variant in player_variants:
        for ext in ['jpg', 'png', 'svg', 'jpeg']:
            path = _find_asset_by_filename(f"{team_abbr}_{player_variant}.{ext}")
            if path:
                return path
    return None

def _build_player_cache():
    """扫描 picture-ab 目录，建立 player_name_lower → abbreviation 映射"""
    global _player_abbr_cache
    if _player_abbr_cache is not None:
        return _player_abbr_cache
    
    _player_abbr_cache = {}
    if not os.path.isdir(PICTURE_DIR):
        return _player_abbr_cache
    
    for f in _list_picture_files():
        # Match: ABBR_PlayerID.ext (e.g. FLCN_ImperialHal.jpg)
        m = re.match(r'^([A-Z0-9]+(?:\.[A-Z0-9]+)?)_(.+?)\.(png|jpg|svg|jpeg)$', f, re.IGNORECASE)
        if m:
            abbr = m.group(1).upper()
            player_id = m.group(2)
            _player_abbr_cache[player_id.lower()] = abbr
            _player_abbr_cache[player_id.replace('_', ' ').lower()] = abbr
    
    return _player_abbr_cache


def get_team_abbr(team_name):
    """
    根据战队名称（任意格式）获取缩写。
    先精确匹配，再模糊匹配，最后尝试从 player 反查。
    返回缩写字符串或 None。
    """
    if not team_name:
        return None
    
    # 1. 精确匹配
    if team_name in EXACT_TEAM_MAP:
        return EXACT_TEAM_MAP[team_name]
    
    # 2. 模糊匹配（小写 + 去空格标准化）
    normalized = re.sub(r'\s+', ' ', team_name.lower().strip())
    if normalized in FUZZY_TEAM_MAP:
        return FUZZY_TEAM_MAP[normalized]
    
    # 3. 部分匹配（CSV队名可能只包含关键字）
    for key, abbr in sorted(FUZZY_TEAM_MAP.items(), key=lambda x: -len(x[0])):
        if key in normalized or normalized in key:
            return abbr
    
    # 4. 从选手反查：查找该队任一选手所在的 abbr
    # (这需要 CSV 中已有 player-team 对应，通常在其他上下文中使用)
    return None


def find_player_photo(player_name, team_name=None, team_abbr=None):
    """
    查找选手照片文件路径。
    
    参数:
        player_name: 选手名（如 "ImperialHal"）
        team_name: 战队全名（可选，用于辅助查找）
        team_abbr: 战队缩写（可选，直接使用）
    
    返回: (file_path, team_abbr) 或 (None, None)
    """
    if not os.path.isdir(PICTURE_DIR):
        return None, None
    
    # Normalize player name for matching
    player_normalized = re.sub(r'\s+', ' ', player_name.lower().strip())
    
    # If we have team_abbr, try direct lookup first
    if team_abbr:
        path = _find_photo_by_abbr_and_player(team_abbr, player_name)
        if path:
            return path, team_abbr
    
    # If we have team_name, get abbr
    if not team_abbr and team_name:
        team_abbr = get_team_abbr(team_name)
        if team_abbr:
            return find_player_photo(player_name, team_abbr=team_abbr)
    
    # Try all player files matching the name across all teams
    cache = _build_player_cache()
    
    # Exact player name match
    if player_normalized in cache:
        abbr = cache[player_normalized]
        path = _find_photo_by_abbr_and_player(abbr, player_name)
        if path:
            return path, abbr
    
    # Fuzzy player name match
    for cached_name, abbr in cache.items():
        # Check if one contains the other
        if player_normalized in cached_name or cached_name in player_normalized:
            # Find the actual file
            for fname in _list_picture_files():
                if fname.lower().startswith(abbr.lower() + '_') and cached_name in fname.lower():
                    path = os.path.join(PICTURE_DIR, fname)
                    if _is_usable_asset(path):
                        return path, abbr
    
    return None, None


def find_team_logo(team_name=None, team_abbr=None):
    """
    查找战队Logo文件路径。
    返回: file_path 或 None
    """
    if not os.path.isdir(PICTURE_DIR):
        return None
    
    # Determine abbreviation
    abbr = team_abbr or (get_team_abbr(team_name) if team_name else None)
    if not abbr:
        return None
    
    for ext in ['png', 'jpg', 'svg']:
        path = os.path.join(PICTURE_DIR, f"{abbr}.{ext}")
        if _is_usable_asset(path):
            return path
    
    return None


def get_player_photo_base64(player_name, team_name=None, team_abbr=None, max_size=(120, 120)):
    """
    获取选手照片的 base64 编码（用于嵌入 HTML/PDF）。
    返回 base64 字符串或 None。
    """
    import base64
    from PIL import Image
    import io
    
    path, _ = find_player_photo(player_name, team_name, team_abbr)
    if not path:
        return None
    
    try:
        img = Image.open(path)
        if max_size:
            img.thumbnail(max_size, Image.LANCZOS)
        buf = io.BytesIO()
        # Always save as PNG for consistency
        img.save(buf, 'PNG')
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None


# ====== 批量爬取功能 ======
def crawl_team_logos_and_photos(url="https://liquipedia.net/apexlegends/Apex_Legends_Global_Series/2026/Split_1/Playoffs/Group_Stage"):
    """
    从 Liquipedia 页面爬取所有战队Logo和选手照片。
    这是独立的功能，可以在 skill 中被调用。
    需要: pip install requests beautifulsoup4
    """
    import requests
    import time
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    session = requests.Session()
    session.headers.update(headers)
    
    os.makedirs(PICTURE_DIR, exist_ok=True)
    
    print("[Crawl] Step 1/2: Downloading team logos...")
    
    # 1. Get team logos from group stage page
    resp = session.get(url, timeout=30)
    html = resp.text
    
    import re as _re
    all_imgs = _re.findall(r'<img\s+([^>]*?)/?>', html)
    
    team_logos = {}
    for img_str in all_imgs:
        src_m = _re.search(r'src="([^"]*)"', img_str)
        alt_m = _re.search(r'alt="([^"]*)"', img_str)
        if not src_m or not alt_m:
            continue
        src = src_m.group(1)
        alt = alt_m.group(1)
        
        if '/commons/images/' not in src:
            continue
        if _re.search(r'/[A-Z][a-z]_hd\.png', src):
            continue
        if 'ALGS' in src or 'APEX' in src or 'liquipedia_icon' in src:
            continue
        if not alt or alt == 'Logo':
            continue
        if alt not in team_logos:
            team_logos[alt] = src
    
    # 2. Extract name → abbreviation mapping
    team_links = _re.findall(r'<a href="/apexlegends/([^"]+)"[^>]*>([^<]+)</a>', html)
    team_pages = {}
    for href, text in team_links:
        if href.startswith(('Category:', 'Special:', 'Main_Page', 'Apex_Legends', 'Liquipedia:')):
            continue
        text = text.strip()
        if not text or text in ['[ edit ]', 'edit']:
            continue
        if href not in team_pages:
            team_pages[href] = []
        if text not in team_pages[href]:
            team_pages[href].append(text)
    
    name_to_abbr_local = {}
    for href, texts in team_pages.items():
        if len(texts) >= 2:
            full = max(texts, key=len)
            abbr = min(texts, key=len).upper()
            skip = ['Challenger Circuits', 'Final', 'POI Drafts', 'Regular Season', 
                    'Stats', 'VODs', 'Pro League', 'Online Open', 'Overview']
            if full not in skip:
                name_to_abbr_local[full] = abbr
    
    # 3. Download team logos
    logo_count = 0
    for team_name, thumb_src in team_logos.items():
        abbr = name_to_abbr_local.get(team_name, team_name.upper().replace(' ', '_'))
        
        full_src = _re.sub(r'/thumb(/[^/]+/[^/]+/[^/]+\.(?:png|svg|jpg|jpeg))/.*$', r'\1', thumb_src)
        img_url = "https://liquipedia.net" + full_src
        
        ext_match = _re.search(r'\.(png|svg|jpg|jpeg)$', full_src, _re.IGNORECASE)
        ext = ext_match.group(1).lower() if ext_match else 'png'
        if ext == 'jpeg':
            ext = 'jpg'
        
        filepath = os.path.join(PICTURE_DIR, f"{abbr}.{ext}")
        if os.path.exists(filepath) and os.path.getsize(filepath) > 5000:
            logo_count += 1
            continue
        
        try:
            img_resp = session.get(img_url, timeout=30)
            if img_resp.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(img_resp.content)
                logo_count += 1
        except Exception:
            pass
        time.sleep(0.2)
    
    print(f"[Crawl] Downloaded {logo_count} team logos")
    
    # 4. Get active players for each team and download photos
    print("[Crawl] Step 2/2: Downloading player photos...")
    photo_count = 0
    
    def safe_get(url, retries=3):
        for attempt in range(retries):
            try:
                return session.get(url, timeout=30)
            except Exception:
                if attempt < retries - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise
    
    def is_player_photo(src):
        if '/commons/images/' not in src:
            return False
        if _re.search(r'/[A-Z][a-z]_hd\.png', src):
            return False
        if _re.search(r'(?:ALGS|APEX|BLGS)[^a-zA-Z]*(?:Icon|icon)_', src):
            return False
        if 'Esports_World_Cup_icon' in src or 'liquipedia_icon' in src:
            return False
        if _re.search(r'(?:lightmode|darkmode|allmode)\.(?:png|svg)', src, _re.IGNORECASE):
            return False
        if _re.search(r'(?:^|/)[^/]*icon\.(?:png|jpg)', src, _re.IGNORECASE):
            return False
        if '_Apex_Legends_Icon' in src or 'Legend_Icon' in src or 'Apex_Legends_default_' in src:
            return False
        return True
    
    for team_name, abbr in name_to_abbr_local.items():
        team_page = team_name.replace(' ', '_')
        
        try:
            resp = safe_get(f"https://liquipedia.net/apexlegends/{team_page}")
            html_t = resp.text
        except Exception:
            continue
        
        active_idx = html_t.find('id="Active"')
        if active_idx == -1:
            continue
        
        remaining = html_t[active_idx+10:]
        next_heading = _re.search(r'<(?:h2|h3)[^>]*id="([^"]*)"', remaining)
        end_idx = active_idx + 10 + next_heading.start() if next_heading else len(html_t)
        active_section = html_t[active_idx:end_idx]
        
        player_links = _re.findall(r'<a href="/apexlegends/([^"]+)"[^>]*>([^<]+)</a>', active_section)
        players = []
        seen = set()
        for href, dn in player_links:
            if href.startswith('index.php') or "\\" in href or "#" in href or href in seen:
                continue
            seen.add(href)
            players.append(href)
        
        for player_id in players:
            # Check if already exists
            exists = False
            for ext in ['jpg', 'png', 'svg']:
                if os.path.exists(os.path.join(PICTURE_DIR, f"{abbr}_{player_id}.{ext}")):
                    if os.path.getsize(os.path.join(PICTURE_DIR, f"{abbr}_{player_id}.{ext}")) > 5000:
                        exists = True
                        photo_count += 1
                        break
            if exists:
                continue
            
            try:
                resp = safe_get(f"https://liquipedia.net/apexlegends/{player_id}")
                html_p = resp.text
            except Exception:
                continue
            
            all_imgs_p = _re.findall(r'<img\s+([^>]*?)/?>', html_p)
            candidates = []
            for img_str in all_imgs_p:
                src_m = _re.search(r'src="([^"]*)"', img_str)
                if src_m and is_player_photo(src_m.group(1)):
                    candidates.append(src_m.group(1))
            
            if not candidates:
                continue
            
            pid_lower = player_id.lower()
            selected = None
            for c in candidates:
                if pid_lower in c.lower():
                    selected = c
                    break
            if not selected:
                selected = candidates[0]
            
            full_src = _re.sub(r'/thumb(/[^/]+/[^/]+/[^/]+\.(?:png|svg|jpg|jpeg))/.*$', r'\1', selected)
            img_url = "https://liquipedia.net" + full_src
            
            ext_match = _re.search(r'\.(png|svg|jpg|jpeg)$', full_src, _re.IGNORECASE)
            ext = ext_match.group(1).lower() if ext_match else 'jpg'
            if ext == 'jpeg':
                ext = 'jpg'
            
            try:
                img_resp = safe_get(img_url)
                if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                    filepath = os.path.join(PICTURE_DIR, f"{abbr}_{player_id}.{ext}")
                    with open(filepath, 'wb') as f:
                        f.write(img_resp.content)
                    photo_count += 1
            except Exception:
                pass
            
            time.sleep(0.15)
        
        time.sleep(0.2)
    
    print(f"[Crawl] Downloaded {photo_count} player photos")
    print(f"[Crawl] Done! Logos: {logo_count}, Photos: {photo_count}")
    return logo_count, photo_count


if __name__ == '__main__':
    # 测试
    print("=== Team Abbr Test ===")
    tests = ["Team Liquid", "liquid", "TLN Pirates", "AURORA", "NinjasinPyjamas", "S8UL", "VK GAMING"]
    for t in tests:
        print(f"  '{t}' → {get_team_abbr(t)}")
    
    print("\n=== Player Photo Test ===")
    test_players = [("ImperialHal", "Team Falcons"), ("Zer0", "Team Liquid"), ("YukaF", "ZETA DIVISION")]
    for pname, tname in test_players:
        path, abbr = find_player_photo(pname, team_name=tname)
        print(f"  {pname} ({tname}) → {path}")
